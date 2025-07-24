#!/usr/bin/env python3
"""
国税庁データ自動取得・更新システム
国税庁ウェブサイトを定期的に監視し、新しいデータを自動で取得・更新する
"""

import requests
import pandas as pd
import sqlite3
import logging
import schedule
import time
import os
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import PyPDF2
import io
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import hashlib

from .tax_data_manager import TaxDataManager

class TaxDataAutoUpdater:
    """国税庁データ自動取得・更新システム"""
    
    def __init__(self, data_manager: TaxDataManager, config: Dict = None):
        self.data_manager = data_manager
        self.config = config or self._get_default_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tax_data_updater.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _get_default_config(self) -> Dict:
        """デフォルト設定を取得"""
        return {
            'base_url': 'https://www.nta.go.jp',
            'comparable_data_url': '/taxanswer/sozoku/4608.htm',
            'dividend_data_url': '/taxanswer/sozoku/4609.htm',
            'company_size_data_url': '/taxanswer/sozoku/4610.htm',
            'check_interval_hours': 24,  # 24時間ごとにチェック
            'download_dir': 'downloads',
            'backup_dir': 'backups',
            'max_retries': 3,
            'timeout': 30
        }
    
    def check_for_updates(self) -> bool:
        """更新の有無をチェック"""
        try:
            self.logger.info("国税庁データの更新チェックを開始")
            
            # 各データタイプの更新チェック
            updates_available = {
                'comparable': self._check_comparable_data_updates(),
                'dividend': self._check_dividend_data_updates(),
                'company_size': self._check_company_size_data_updates()
            }
            
            has_updates = any(updates_available.values())
            
            if has_updates:
                self.logger.info(f"更新が検出されました: {updates_available}")
                return True
            else:
                self.logger.info("更新はありません")
                return False
                
        except Exception as e:
            self.logger.error(f"更新チェック中にエラーが発生: {e}")
            return False
    
    def _check_comparable_data_updates(self) -> bool:
        """類似業種比準価額データの更新チェック"""
        try:
            url = urljoin(self.config['base_url'], self.config['comparable_data_url'])
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # ページの最終更新日を取得
            last_updated = self._extract_last_updated_date(soup)
            
            # データベースの最新データと比較
            latest_db_data = self._get_latest_comparable_data()
            
            if not latest_db_data or last_updated > latest_db_data:
                self.logger.info(f"類似業種データの更新が検出されました: {last_updated}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"類似業種データの更新チェックに失敗: {e}")
            return False
    
    def _check_dividend_data_updates(self) -> bool:
        """配当還元率データの更新チェック"""
        try:
            url = urljoin(self.config['base_url'], self.config['dividend_data_url'])
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            last_updated = self._extract_last_updated_date(soup)
            
            latest_db_data = self._get_latest_dividend_data()
            
            if not latest_db_data or last_updated > latest_db_data:
                self.logger.info(f"配当還元率データの更新が検出されました: {last_updated}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"配当還元率データの更新チェックに失敗: {e}")
            return False
    
    def _check_company_size_data_updates(self) -> bool:
        """会社規模判定基準データの更新チェック"""
        try:
            url = urljoin(self.config['base_url'], self.config['company_size_data_url'])
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            last_updated = self._extract_last_updated_date(soup)
            
            latest_db_data = self._get_latest_company_size_data()
            
            if not latest_db_data or last_updated > latest_db_data:
                self.logger.info(f"会社規模判定基準データの更新が検出されました: {last_updated}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"会社規模判定基準データの更新チェックに失敗: {e}")
            return False
    
    def _extract_last_updated_date(self, soup: BeautifulSoup) -> date:
        """ページから最終更新日を抽出"""
        try:
            # 一般的な更新日表示パターンを検索
            patterns = [
                r'最終更新日[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'更新日[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})年(\d{1,2})月(\d{1,2})日.*更新',
                r'(\d{4})/(\d{1,2})/(\d{1,2})'
            ]
            
            text = soup.get_text()
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        return date(int(year), int(month), int(day))
            
            # 見つからない場合は現在日付を返す
            return date.today()
            
        except Exception as e:
            self.logger.warning(f"更新日の抽出に失敗: {e}")
            return date.today()
    
    def _get_latest_comparable_data(self) -> Optional[date]:
        """データベースの最新類似業種データ日付を取得"""
        try:
            with sqlite3.connect(self.data_manager.db_path) as conn:
                cursor = conn.execute('''
                    SELECT MAX(year), MAX(month) FROM comparable_industry_data
                ''')
                row = cursor.fetchone()
                if row and row[0] and row[1]:
                    return date(row[0], row[1], 1)
            return None
        except Exception as e:
            self.logger.error(f"最新データ日付の取得に失敗: {e}")
            return None
    
    def _get_latest_dividend_data(self) -> Optional[date]:
        """データベースの最新配当還元率データ日付を取得"""
        try:
            with sqlite3.connect(self.data_manager.db_path) as conn:
                cursor = conn.execute('''
                    SELECT MAX(year), MAX(month) FROM dividend_reduction_rates
                ''')
                row = cursor.fetchone()
                if row and row[0] and row[1]:
                    return date(row[0], row[1], 1)
            return None
        except Exception as e:
            self.logger.error(f"最新データ日付の取得に失敗: {e}")
            return None
    
    def _get_latest_company_size_data(self) -> Optional[date]:
        """データベースの最新会社規模判定基準データ日付を取得"""
        try:
            with sqlite3.connect(self.data_manager.db_path) as conn:
                cursor = conn.execute('''
                    SELECT MAX(year), MAX(month) FROM company_size_criteria
                ''')
                row = cursor.fetchone()
                if row and row[0] and row[1]:
                    return date(row[0], row[1], 1)
            return None
        except Exception as e:
            self.logger.error(f"最新データ日付の取得に失敗: {e}")
            return None
    
    def download_and_process_data(self) -> bool:
        """データのダウンロードと処理"""
        try:
            self.logger.info("データのダウンロードと処理を開始")
            
            # ダウンロードディレクトリの作成
            download_dir = Path(self.config['download_dir'])
            download_dir.mkdir(exist_ok=True)
            
            success = True
            
            # 類似業種データのダウンロードと処理
            if self._check_comparable_data_updates():
                success &= self._download_and_process_comparable_data(download_dir)
            
            # 配当還元率データのダウンロードと処理
            if self._check_dividend_data_updates():
                success &= self._download_and_process_dividend_data(download_dir)
            
            # 会社規模判定基準データのダウンロードと処理
            if self._check_company_size_data_updates():
                success &= self._download_and_process_company_size_data(download_dir)
            
            if success:
                self.logger.info("データのダウンロードと処理が完了しました")
                self._create_backup()
            
            return success
            
        except Exception as e:
            self.logger.error(f"データのダウンロードと処理に失敗: {e}")
            return False
    
    def _download_and_process_comparable_data(self, download_dir: Path) -> bool:
        """類似業種データのダウンロードと処理"""
        try:
            # PDFファイルのダウンロード
            pdf_url = self._find_comparable_data_pdf_url()
            if not pdf_url:
                self.logger.error("類似業種データのPDF URLが見つかりません")
                return False
            
            pdf_path = download_dir / f"comparable_data_{datetime.now().strftime('%Y%m%d')}.pdf"
            if self._download_file(pdf_url, pdf_path):
                # PDFからCSVに変換
                csv_path = self._convert_pdf_to_csv(pdf_path, 'comparable')
                if csv_path:
                    # データベースにインポート
                    current_date = date.today()
                    return self.data_manager.import_comparable_industry_data(
                        str(csv_path), current_date.year, current_date.month
                    )
            
            return False
            
        except Exception as e:
            self.logger.error(f"類似業種データの処理に失敗: {e}")
            return False
    
    def _download_and_process_dividend_data(self, download_dir: Path) -> bool:
        """配当還元率データのダウンロードと処理"""
        try:
            pdf_url = self._find_dividend_data_pdf_url()
            if not pdf_url:
                self.logger.error("配当還元率データのPDF URLが見つかりません")
                return False
            
            pdf_path = download_dir / f"dividend_data_{datetime.now().strftime('%Y%m%d')}.pdf"
            if self._download_file(pdf_url, pdf_path):
                csv_path = self._convert_pdf_to_csv(pdf_path, 'dividend')
                if csv_path:
                    current_date = date.today()
                    return self.data_manager.import_dividend_reduction_rates(
                        str(csv_path), current_date.year, current_date.month
                    )
            
            return False
            
        except Exception as e:
            self.logger.error(f"配当還元率データの処理に失敗: {e}")
            return False
    
    def _download_and_process_company_size_data(self, download_dir: Path) -> bool:
        """会社規模判定基準データのダウンロードと処理"""
        try:
            pdf_url = self._find_company_size_data_pdf_url()
            if not pdf_url:
                self.logger.error("会社規模判定基準データのPDF URLが見つかりません")
                return False
            
            pdf_path = download_dir / f"company_size_data_{datetime.now().strftime('%Y%m%d')}.pdf"
            if self._download_file(pdf_url, pdf_path):
                csv_path = self._convert_pdf_to_csv(pdf_path, 'company_size')
                if csv_path:
                    current_date = date.today()
                    return self.data_manager.import_company_size_criteria(
                        str(csv_path), current_date.year, current_date.month
                    )
            
            return False
            
        except Exception as e:
            self.logger.error(f"会社規模判定基準データの処理に失敗: {e}")
            return False
    
    def _find_comparable_data_pdf_url(self) -> Optional[str]:
        """類似業種データのPDF URLを検索"""
        try:
            url = urljoin(self.config['base_url'], self.config['comparable_data_url'])
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # PDFリンクを検索
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf') and '類似業種' in link.get_text():
                    return urljoin(url, href)
            
            return None
            
        except Exception as e:
            self.logger.error(f"類似業種データPDF URLの検索に失敗: {e}")
            return None
    
    def _find_dividend_data_pdf_url(self) -> Optional[str]:
        """配当還元率データのPDF URLを検索"""
        try:
            url = urljoin(self.config['base_url'], self.config['dividend_data_url'])
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf') and '配当還元' in link.get_text():
                    return urljoin(url, href)
            
            return None
            
        except Exception as e:
            self.logger.error(f"配当還元率データPDF URLの検索に失敗: {e}")
            return None
    
    def _find_company_size_data_pdf_url(self) -> Optional[str]:
        """会社規模判定基準データのPDF URLを検索"""
        try:
            url = urljoin(self.config['base_url'], self.config['company_size_data_url'])
            response = self.session.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.endswith('.pdf') and '会社規模' in link.get_text():
                    return urljoin(url, href)
            
            return None
            
        except Exception as e:
            self.logger.error(f"会社規模判定基準データPDF URLの検索に失敗: {e}")
            return None
    
    def _download_file(self, url: str, file_path: Path) -> bool:
        """ファイルのダウンロード"""
        try:
            for attempt in range(self.config['max_retries']):
                try:
                    response = self.session.get(url, timeout=self.config['timeout'])
                    response.raise_for_status()
                    
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    self.logger.info(f"ファイルをダウンロードしました: {file_path}")
                    return True
                    
                except requests.RequestException as e:
                    self.logger.warning(f"ダウンロード試行 {attempt + 1} に失敗: {e}")
                    if attempt < self.config['max_retries'] - 1:
                        time.sleep(2 ** attempt)  # 指数バックオフ
            
            return False
            
        except Exception as e:
            self.logger.error(f"ファイルダウンロードに失敗: {e}")
            return False
    
    def _convert_pdf_to_csv(self, pdf_path: Path, data_type: str) -> Optional[Path]:
        """PDFからCSVへの変換"""
        try:
            csv_path = pdf_path.with_suffix('.csv')
            
            # PDFの読み込み
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # テキストの抽出
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                # データタイプに応じた変換
                if data_type == 'comparable':
                    df = self._parse_comparable_data(text)
                elif data_type == 'dividend':
                    df = self._parse_dividend_data(text)
                elif data_type == 'company_size':
                    df = self._parse_company_size_data(text)
                else:
                    raise ValueError(f"未知のデータタイプ: {data_type}")
                
                # CSVとして保存
                df.to_csv(csv_path, index=False, encoding='utf-8')
                self.logger.info(f"PDFをCSVに変換しました: {csv_path}")
                
                return csv_path
                
        except Exception as e:
            self.logger.error(f"PDFからCSVへの変換に失敗: {e}")
            return None
    
    def _parse_comparable_data(self, text: str) -> pd.DataFrame:
        """類似業種データの解析"""
        # 実際のPDF構造に応じて実装
        # ここではサンプル実装
        data = []
        lines = text.split('\n')
        
        for line in lines:
            if re.match(r'\d+', line.strip()):
                parts = line.split()
                if len(parts) >= 5:
                    data.append({
                        'industry_code': parts[0],
                        'industry_name': parts[1],
                        'average_price': float(parts[2]),
                        'average_dividend': float(parts[3]),
                        'average_profit': float(parts[4]),
                        'average_net_assets': float(parts[5]) if len(parts) > 5 else 0
                    })
        
        return pd.DataFrame(data)
    
    def _parse_dividend_data(self, text: str) -> pd.DataFrame:
        """配当還元率データの解析"""
        data = []
        lines = text.split('\n')
        
        for line in lines:
            if re.match(r'\d+', line.strip()):
                parts = line.split()
                if len(parts) >= 3:
                    data.append({
                        'capital_range_min': int(parts[0]),
                        'capital_range_max': int(parts[1]),
                        'reduction_rate': float(parts[2])
                    })
        
        return pd.DataFrame(data)
    
    def _parse_company_size_data(self, text: str) -> pd.DataFrame:
        """会社規模判定基準データの解析"""
        data = []
        lines = text.split('\n')
        
        for line in lines:
            if re.match(r'\w+', line.strip()):
                parts = line.split()
                if len(parts) >= 7:
                    data.append({
                        'industry_type': parts[0],
                        'size_category': parts[1],
                        'employee_min': int(parts[2]),
                        'employee_max': int(parts[3]),
                        'asset_min': int(parts[4]),
                        'asset_max': int(parts[5]),
                        'sales_min': int(parts[6]),
                        'sales_max': int(parts[7]) if len(parts) > 7 else 999999999
                    })
        
        return pd.DataFrame(data)
    
    def _create_backup(self):
        """データベースのバックアップを作成"""
        try:
            backup_dir = Path(self.config['backup_dir'])
            backup_dir.mkdir(exist_ok=True)
            
            backup_path = backup_dir / f"tax_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            
            with sqlite3.connect(self.data_manager.db_path) as source_conn:
                with sqlite3.connect(backup_path) as backup_conn:
                    source_conn.backup(backup_conn)
            
            self.logger.info(f"バックアップを作成しました: {backup_path}")
            
        except Exception as e:
            self.logger.error(f"バックアップの作成に失敗: {e}")
    
    def start_scheduler(self):
        """スケジューラーを開始"""
        try:
            self.logger.info("自動更新スケジューラーを開始")
            
            # 毎日指定時間にチェック
            schedule.every(self.config['check_interval_hours']).hours.do(self._scheduled_check)
            
            # 初回チェックを即座に実行
            self._scheduled_check()
            
            # スケジューラーを実行
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
                
        except KeyboardInterrupt:
            self.logger.info("スケジューラーを停止しました")
        except Exception as e:
            self.logger.error(f"スケジューラーでエラーが発生: {e}")
    
    def _scheduled_check(self):
        """スケジュールされたチェック"""
        try:
            self.logger.info("スケジュールされた更新チェックを実行")
            
            if self.check_for_updates():
                self.download_and_process_data()
            
        except Exception as e:
            self.logger.error(f"スケジュールされたチェックでエラーが発生: {e}")
    
    def manual_update(self) -> bool:
        """手動更新の実行"""
        try:
            self.logger.info("手動更新を実行")
            return self.download_and_process_data()
        except Exception as e:
            self.logger.error(f"手動更新でエラーが発生: {e}")
            return False 
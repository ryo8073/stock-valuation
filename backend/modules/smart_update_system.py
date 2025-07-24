#!/usr/bin/env python3
"""
インテリジェント国税庁データ更新システム
サーバー負荷を最小化し、確実なデータ更新を実現
"""

import requests
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3

from .tax_data_manager import TaxDataManager

class SmartUpdateSystem:
    """インテリジェントな更新システム"""
    
    def __init__(self, data_manager: TaxDataManager, config: Dict = None):
        self.data_manager = data_manager
        self.config = config or self._get_default_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StockValuatorPro/1.0 (https://stock-valuator-pro.com)'
        })
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('smart_update.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 更新履歴の初期化
        self._init_update_history()
    
    def _get_default_config(self) -> Dict:
        """デフォルト設定"""
        return {
            'base_url': 'https://www.nta.go.jp',
            'check_interval_hours': 168,  # 週1回
            'lightweight_check': True,
            'notification_enabled': True,
            'auto_update': False,  # 手動承認のみ
            'max_retries': 3,
            'timeout': 10,  # 軽量チェック用短縮タイムアウト
            'notification_email': 'admin@stock-valuator-pro.com',
            'notification_slack_webhook': None
        }
    
    def _init_update_history(self):
        """更新履歴テーブルの初期化"""
        with sqlite3.connect(self.data_manager.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS update_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_type TEXT NOT NULL,
                    last_modified TEXT,
                    etag TEXT,
                    content_hash TEXT,
                    update_available BOOLEAN DEFAULT FALSE,
                    update_status TEXT DEFAULT 'pending',
                    admin_approved BOOLEAN DEFAULT FALSE,
                    update_executed_at TIMESTAMP,
                    notes TEXT
                )
            ''')
            conn.commit()
    
    def smart_check(self) -> Dict[str, bool]:
        """インテリジェントな更新チェック"""
        try:
            self.logger.info("インテリジェント更新チェックを開始")
            
            results = {}
            
            # 各データタイプの軽量チェック
            for data_type in ['comparable', 'dividend', 'company_size']:
                update_available = self._lightweight_check(data_type)
                results[data_type] = update_available
                
                if update_available:
                    self._notify_update_available(data_type)
                    self._record_update_history(data_type, True)
                else:
                    self._record_update_history(data_type, False)
            
            return results
            
        except Exception as e:
            self.logger.error(f"スマートチェック中にエラー: {e}")
            return {}
    
    def _lightweight_check(self, data_type: str) -> bool:
        """軽量な更新チェック（HEADリクエスト）"""
        try:
            url = self._get_data_url(data_type)
            
            # HEADリクエストで軽量チェック
            response = self.session.head(url, timeout=self.config['timeout'])
            response.raise_for_status()
            
            # 前回のチェック結果と比較
            last_check = self._get_last_check_info(data_type)
            
            if not last_check:
                # 初回チェック
                self.logger.info(f"{data_type}: 初回チェック")
                return True
            
            # Last-Modifiedヘッダーの比較
            last_modified = response.headers.get('Last-Modified')
            if last_modified and last_modified != last_check.get('last_modified'):
                self.logger.info(f"{data_type}: Last-Modifiedが変更されました")
                return True
            
            # ETagヘッダーの比較
            etag = response.headers.get('ETag')
            if etag and etag != last_check.get('etag'):
                self.logger.info(f"{data_type}: ETagが変更されました")
                return True
            
            # 一定期間経過後の強制チェック
            last_check_date = datetime.fromisoformat(last_check['check_date'])
            if datetime.now() - last_check_date > timedelta(days=30):
                self.logger.info(f"{data_type}: 30日経過による強制チェック")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"{data_type}の軽量チェックでエラー: {e}")
            return False
    
    def _get_data_url(self, data_type: str) -> str:
        """データタイプに応じたURL取得"""
        urls = {
            'comparable': '/taxanswer/sozoku/4608.htm',
            'dividend': '/taxanswer/sozoku/4609.htm',
            'company_size': '/taxanswer/sozoku/4610.htm'
        }
        return f"{self.config['base_url']}{urls[data_type]}"
    
    def _get_last_check_info(self, data_type: str) -> Optional[Dict]:
        """前回のチェック情報取得"""
        with sqlite3.connect(self.data_manager.db_path) as conn:
            cursor = conn.execute('''
                SELECT check_date, last_modified, etag, content_hash
                FROM update_history
                WHERE data_type = ?
                ORDER BY check_date DESC
                LIMIT 1
            ''', (data_type,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'check_date': row[0],
                    'last_modified': row[1],
                    'etag': row[2],
                    'content_hash': row[3]
                }
            return None
    
    def _record_update_history(self, data_type: str, update_available: bool):
        """更新履歴の記録"""
        with sqlite3.connect(self.data_manager.db_path) as conn:
            conn.execute('''
                INSERT INTO update_history 
                (data_type, update_available, update_status)
                VALUES (?, ?, ?)
            ''', (data_type, update_available, 'pending'))
            conn.commit()
    
    def _notify_update_available(self, data_type: str):
        """更新利用可能時の通知"""
        if not self.config['notification_enabled']:
            return
        
        message = f"""
        国税庁データ更新通知
        
        データタイプ: {data_type}
        更新日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        管理画面から更新を承認してください。
        URL: https://admin.stock-valuator-pro.com/updates
        """
        
        # メール通知
        if self.config.get('notification_email'):
            self._send_email_notification(message)
        
        # Slack通知
        if self.config.get('notification_slack_webhook'):
            self._send_slack_notification(message)
    
    def _send_email_notification(self, message: str):
        """メール通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = 'noreply@stock-valuator-pro.com'
            msg['To'] = self.config['notification_email']
            msg['Subject'] = '国税庁データ更新通知'
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # SMTP設定（実際の環境に応じて設定）
            # smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
            # smtp_server.starttls()
            # smtp_server.login('username', 'password')
            # smtp_server.send_message(msg)
            # smtp_server.quit()
            
            self.logger.info("メール通知を送信しました")
            
        except Exception as e:
            self.logger.error(f"メール通知送信エラー: {e}")
    
    def _send_slack_notification(self, message: str):
        """Slack通知"""
        try:
            webhook_url = self.config['notification_slack_webhook']
            payload = {
                'text': message,
                'username': 'Stock Valuator Pro',
                'icon_emoji': ':chart_with_upwards_trend:'
            }
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            self.logger.info("Slack通知を送信しました")
            
        except Exception as e:
            self.logger.error(f"Slack通知送信エラー: {e}")
    
    def approve_update(self, data_type: str, admin_user: str) -> bool:
        """管理者による更新承認"""
        try:
            self.logger.info(f"{data_type}の更新を承認: {admin_user}")
            
            # 更新履歴を承認済みに更新
            with sqlite3.connect(self.data_manager.db_path) as conn:
                conn.execute('''
                    UPDATE update_history
                    SET admin_approved = TRUE, update_status = 'approved'
                    WHERE data_type = ? AND update_available = TRUE
                    ORDER BY check_date DESC
                    LIMIT 1
                ''', (data_type,))
                conn.commit()
            
            # 実際の更新を実行
            success = self._execute_update(data_type)
            
            if success:
                self._record_update_execution(data_type)
                self.logger.info(f"{data_type}の更新が完了しました")
            else:
                self.logger.error(f"{data_type}の更新に失敗しました")
            
            return success
            
        except Exception as e:
            self.logger.error(f"更新承認処理でエラー: {e}")
            return False
    
    def _execute_update(self, data_type: str) -> bool:
        """実際の更新実行"""
        try:
            # 既存の自動更新システムを呼び出し
            from .tax_data_auto_updater import TaxDataAutoUpdater
            
            updater = TaxDataAutoUpdater(self.data_manager, self.config)
            
            if data_type == 'comparable':
                return updater._download_and_process_comparable_data(Path('downloads'))
            elif data_type == 'dividend':
                return updater._download_and_process_dividend_data(Path('downloads'))
            elif data_type == 'company_size':
                return updater._download_and_process_company_size_data(Path('downloads'))
            
            return False
            
        except Exception as e:
            self.logger.error(f"更新実行でエラー: {e}")
            return False
    
    def _record_update_execution(self, data_type: str):
        """更新実行の記録"""
        with sqlite3.connect(self.data_manager.db_path) as conn:
            conn.execute('''
                UPDATE update_history
                SET update_status = 'completed', update_executed_at = CURRENT_TIMESTAMP
                WHERE data_type = ? AND admin_approved = TRUE
                ORDER BY check_date DESC
                LIMIT 1
            ''', (data_type,))
            conn.commit()
    
    def get_update_status(self) -> Dict[str, Dict]:
        """更新状況の取得"""
        with sqlite3.connect(self.data_manager.db_path) as conn:
            cursor = conn.execute('''
                SELECT data_type, update_available, update_status, 
                       admin_approved, check_date, update_executed_at
                FROM update_history
                WHERE check_date = (
                    SELECT MAX(check_date) 
                    FROM update_history h2 
                    WHERE h2.data_type = update_history.data_type
                )
            ''')
            
            results = {}
            for row in cursor.fetchall():
                results[row[0]] = {
                    'update_available': row[1],
                    'status': row[2],
                    'admin_approved': row[3],
                    'check_date': row[4],
                    'update_executed_at': row[5]
                }
            
            return results
    
    def get_update_history(self, data_type: str = None, limit: int = 10) -> List[Dict]:
        """更新履歴の取得"""
        with sqlite3.connect(self.data_manager.db_path) as conn:
            if data_type:
                cursor = conn.execute('''
                    SELECT * FROM update_history
                    WHERE data_type = ?
                    ORDER BY check_date DESC
                    LIMIT ?
                ''', (data_type, limit))
            else:
                cursor = conn.execute('''
                    SELECT * FROM update_history
                    ORDER BY check_date DESC
                    LIMIT ?
                ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()] 
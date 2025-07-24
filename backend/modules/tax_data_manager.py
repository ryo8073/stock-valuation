import sqlite3
import json
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import logging

class TaxDataManager:
    """国税庁データ管理システム"""
    
    def __init__(self, db_path: str = "tax_data.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """データベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            # 類似業種比準価額データテーブル
            conn.execute('''
                CREATE TABLE IF NOT EXISTS comparable_industry_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    industry_code TEXT NOT NULL,
                    industry_name TEXT NOT NULL,
                    average_price REAL NOT NULL,
                    average_dividend REAL NOT NULL,
                    average_profit REAL NOT NULL,
                    average_net_assets REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(year, month, industry_code)
                )
            ''')
            
            # 配当還元率データテーブル
            conn.execute('''
                CREATE TABLE IF NOT EXISTS dividend_reduction_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    capital_range_min INTEGER NOT NULL,
                    capital_range_max INTEGER NOT NULL,
                    reduction_rate REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(year, month, capital_range_min, capital_range_max)
                )
            ''')
            
            # 会社規模判定基準テーブル
            conn.execute('''
                CREATE TABLE IF NOT EXISTS company_size_criteria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    industry_type TEXT NOT NULL,
                    size_category TEXT NOT NULL,
                    employee_min INTEGER,
                    employee_max INTEGER,
                    asset_min INTEGER,
                    asset_max INTEGER,
                    sales_min INTEGER,
                    sales_max INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(year, month, industry_type, size_category)
                )
            ''')
            
            conn.commit()
    
    def import_comparable_industry_data(self, file_path: str, year: int, month: int) -> bool:
        """
        国税庁の類似業種比準価額データをインポート
        
        Args:
            file_path: CSVファイルのパス
            year: データの年
            month: データの月
            
        Returns:
            bool: インポート成功時True
        """
        try:
            # CSVファイルを読み込み
            df = pd.read_csv(file_path, encoding='utf-8')
            
            with sqlite3.connect(self.db_path) as conn:
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO comparable_industry_data 
                        (year, month, industry_code, industry_name, average_price, 
                         average_dividend, average_profit, average_net_assets)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        year, month,
                        row['industry_code'],
                        row['industry_name'],
                        row['average_price'],
                        row['average_dividend'],
                        row['average_profit'],
                        row['average_net_assets']
                    ))
                conn.commit()
            
            logging.info(f"類似業種比準価額データをインポートしました: {year}年{month}月")
            return True
            
        except Exception as e:
            logging.error(f"類似業種比準価額データのインポートに失敗: {e}")
            return False
    
    def import_dividend_reduction_rates(self, file_path: str, year: int, month: int) -> bool:
        """
        配当還元率データをインポート
        
        Args:
            file_path: CSVファイルのパス
            year: データの年
            month: データの月
            
        Returns:
            bool: インポート成功時True
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            with sqlite3.connect(self.db_path) as conn:
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO dividend_reduction_rates 
                        (year, month, capital_range_min, capital_range_max, reduction_rate)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        year, month,
                        row['capital_range_min'],
                        row['capital_range_max'],
                        row['reduction_rate']
                    ))
                conn.commit()
            
            logging.info(f"配当還元率データをインポートしました: {year}年{month}月")
            return True
            
        except Exception as e:
            logging.error(f"配当還元率データのインポートに失敗: {e}")
            return False
    
    def import_company_size_criteria(self, file_path: str, year: int, month: int) -> bool:
        """
        会社規模判定基準データをインポート
        
        Args:
            file_path: CSVファイルのパス
            year: データの年
            month: データの月
            
        Returns:
            bool: インポート成功時True
        """
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            
            with sqlite3.connect(self.db_path) as conn:
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT OR REPLACE INTO company_size_criteria 
                        (year, month, industry_type, size_category, 
                         employee_min, employee_max, asset_min, asset_max, 
                         sales_min, sales_max)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        year, month,
                        row['industry_type'],
                        row['size_category'],
                        row['employee_min'],
                        row['employee_max'],
                        row['asset_min'],
                        row['asset_max'],
                        row['sales_min'],
                        row['sales_max']
                    ))
                conn.commit()
            
            logging.info(f"会社規模判定基準データをインポートしました: {year}年{month}月")
            return True
            
        except Exception as e:
            logging.error(f"会社規模判定基準データのインポートに失敗: {e}")
            return False
    
    def get_comparable_industry_data(self, industry_code: str, target_date: date) -> Optional[Dict]:
        """
        指定日時点の類似業種比準価額データを取得
        
        Args:
            industry_code: 業種コード
            target_date: 対象日
            
        Returns:
            Dict: 類似業種データ（見つからない場合はNone）
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT average_price, average_dividend, average_profit, average_net_assets
                FROM comparable_industry_data
                WHERE industry_code = ? AND 
                      (year < ? OR (year = ? AND month <= ?))
                ORDER BY year DESC, month DESC
                LIMIT 1
            ''', (industry_code, target_date.year, target_date.year, target_date.month))
            
            row = cursor.fetchone()
            if row:
                return {
                    'price': row[0],
                    'dividend': row[1],
                    'profit': row[2],
                    'net_assets': row[3]
                }
            return None
    
    def get_dividend_reduction_rate(self, capital_amount: int, target_date: date) -> float:
        """
        指定日時点の配当還元率を取得
        
        Args:
            capital_amount: 資本金等の額
            target_date: 対象日
            
        Returns:
            float: 配当還元率
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT reduction_rate
                FROM dividend_reduction_rates
                WHERE capital_range_min <= ? AND capital_range_max >= ? AND
                      (year < ? OR (year = ? AND month <= ?))
                ORDER BY year DESC, month DESC
                LIMIT 1
            ''', (capital_amount, capital_amount, target_date.year, target_date.year, target_date.month))
            
            row = cursor.fetchone()
            return row[0] if row else 0.10  # デフォルト値
    
    def get_company_size_criteria(self, industry_type: str, target_date: date) -> Dict:
        """
        指定日時点の会社規模判定基準を取得
        
        Args:
            industry_type: 業種タイプ
            target_date: 対象日
            
        Returns:
            Dict: 会社規模判定基準
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT size_category, employee_min, employee_max, 
                       asset_min, asset_max, sales_min, sales_max
                FROM company_size_criteria
                WHERE industry_type = ? AND 
                      (year < ? OR (year = ? AND month <= ?))
                ORDER BY year DESC, month DESC
            ''', (industry_type, target_date.year, target_date.year, target_date.month))
            
            criteria = {}
            for row in cursor.fetchall():
                criteria[row[0]] = {
                    'employee_min': row[1],
                    'employee_max': row[2],
                    'asset_min': row[3],
                    'asset_max': row[4],
                    'sales_min': row[5],
                    'sales_max': row[6]
                }
            return criteria
    
    def get_available_data_periods(self) -> List[Tuple[int, int]]:
        """
        利用可能なデータ期間を取得
        
        Returns:
            List[Tuple[int, int]]: (年, 月)のリスト
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT DISTINCT year, month
                FROM comparable_industry_data
                ORDER BY year DESC, month DESC
            ''')
            
            return [(row[0], row[1]) for row in cursor.fetchall()]
    
    def export_data_for_period(self, year: int, month: int, output_dir: str) -> bool:
        """
        指定期間のデータをエクスポート
        
        Args:
            year: 年
            month: 月
            output_dir: 出力ディレクトリ
            
        Returns:
            bool: エクスポート成功時True
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 類似業種データのエクスポート
                comparable_df = pd.read_sql_query('''
                    SELECT * FROM comparable_industry_data 
                    WHERE year = ? AND month = ?
                ''', conn, params=(year, month))
                
                comparable_df.to_csv(f"{output_dir}/comparable_industry_{year}_{month:02d}.csv", 
                                   index=False, encoding='utf-8')
                
                # 配当還元率データのエクスポート
                dividend_df = pd.read_sql_query('''
                    SELECT * FROM dividend_reduction_rates 
                    WHERE year = ? AND month = ?
                ''', conn, params=(year, month))
                
                dividend_df.to_csv(f"{output_dir}/dividend_reduction_{year}_{month:02d}.csv", 
                                 index=False, encoding='utf-8')
                
                # 会社規模判定基準データのエクスポート
                size_df = pd.read_sql_query('''
                    SELECT * FROM company_size_criteria 
                    WHERE year = ? AND month = ?
                ''', conn, params=(year, month))
                
                size_df.to_csv(f"{output_dir}/company_size_{year}_{month:02d}.csv", 
                             index=False, encoding='utf-8')
            
            logging.info(f"データをエクスポートしました: {year}年{month}月")
            return True
            
        except Exception as e:
            logging.error(f"データのエクスポートに失敗: {e}")
            return False
    
    def cleanup_old_data(self, keep_months: int = 60) -> int:
        """
        古いデータを削除
        
        Args:
            keep_months: 保持する月数
            
        Returns:
            int: 削除されたレコード数
        """
        with sqlite3.connect(self.db_path) as conn:
            # 60ヶ月（5年）より古いデータを削除
            cursor = conn.execute('''
                DELETE FROM comparable_industry_data 
                WHERE created_at < datetime('now', '-{} months')
            '''.format(keep_months))
            
            comparable_deleted = cursor.rowcount
            
            cursor = conn.execute('''
                DELETE FROM dividend_reduction_rates 
                WHERE created_at < datetime('now', '-{} months')
            '''.format(keep_months))
            
            dividend_deleted = cursor.rowcount
            
            cursor = conn.execute('''
                DELETE FROM company_size_criteria 
                WHERE created_at < datetime('now', '-{} months')
            '''.format(keep_months))
            
            size_deleted = cursor.rowcount
            
            conn.commit()
            
            total_deleted = comparable_deleted + dividend_deleted + size_deleted
            logging.info(f"古いデータを削除しました: {total_deleted}件")
            return total_deleted 
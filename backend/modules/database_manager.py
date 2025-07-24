#!/usr/bin/env python3
"""
Vercel Postgres データベースマネージャー
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import json

class DatabaseManager:
    """Vercel Postgresデータベース管理クラス"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.logger = logging.getLogger(__name__)
    
    def get_connection(self):
        """データベース接続を取得"""
        return psycopg2.connect(
            self.database_url,
            cursor_factory=RealDictCursor
        )
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """クエリを実行して結果を取得"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    return []
    
    def execute_single_query(self, query: str, params: tuple = None) -> Optional[Dict]:
        """単一レコードを取得するクエリを実行"""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    row = cursor.fetchone()
                    return dict(row) if row else None
                else:
                    conn.commit()
                    return None
    
    def insert_record(self, table: str, data: Dict) -> int:
        """レコードを挿入してIDを返す"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = tuple(data.values())
        
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            RETURNING id
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                result = cursor.fetchone()
                conn.commit()
                return result['id'] if result else None
    
    def update_record(self, table: str, data: Dict, condition: Dict) -> bool:
        """レコードを更新"""
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        
        query = f"""
            UPDATE {table}
            SET {set_clause}
            WHERE {where_clause}
        """
        
        values = tuple(list(data.values()) + list(condition.values()))
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
    
    def delete_record(self, table: str, condition: Dict) -> bool:
        """レコードを削除"""
        where_clause = ' AND '.join([f"{k} = %s" for k in condition.keys()])
        values = tuple(condition.values())
        
        query = f"DELETE FROM {table} WHERE {where_clause}"
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
    
    # 類似業種比準価額データ関連
    def get_comparable_industry_data(self, year: int = None, month: int = None) -> List[Dict]:
        """類似業種比準価額データを取得"""
        if year and month:
            query = """
                SELECT * FROM comparable_industry_data
                WHERE year = %s AND month = %s
                ORDER BY industry_code
            """
            return self.execute_query(query, (year, month))
        else:
            query = """
                SELECT * FROM comparable_industry_data
                ORDER BY year DESC, month DESC, industry_code
            """
            return self.execute_query(query)
    
    def insert_comparable_industry_data(self, data: List[Dict]) -> int:
        """類似業種比準価額データを一括挿入"""
        inserted_count = 0
        
        for record in data:
            try:
                self.insert_record('comparable_industry_data', record)
                inserted_count += 1
            except Exception as e:
                self.logger.error(f"Error inserting comparable industry data: {e}")
        
        return inserted_count
    
    def update_comparable_industry_data(self, year: int, month: int, data: List[Dict]) -> int:
        """類似業種比準価額データを更新"""
        # 既存データを削除
        self.execute_query(
            "DELETE FROM comparable_industry_data WHERE year = %s AND month = %s",
            (year, month)
        )
        
        # 新しいデータを挿入
        return self.insert_comparable_industry_data(data)
    
    # 配当還元率データ関連
    def get_dividend_reduction_rates(self, year: int = None, month: int = None) -> List[Dict]:
        """配当還元率データを取得"""
        if year and month:
            query = """
                SELECT * FROM dividend_reduction_rates
                WHERE year = %s AND month = %s
                ORDER BY capital_range_min
            """
            return self.execute_query(query, (year, month))
        else:
            query = """
                SELECT * FROM dividend_reduction_rates
                ORDER BY year DESC, month DESC, capital_range_min
            """
            return self.execute_query(query)
    
    def insert_dividend_reduction_rates(self, data: List[Dict]) -> int:
        """配当還元率データを一括挿入"""
        inserted_count = 0
        
        for record in data:
            try:
                self.insert_record('dividend_reduction_rates', record)
                inserted_count += 1
            except Exception as e:
                self.logger.error(f"Error inserting dividend reduction rate: {e}")
        
        return inserted_count
    
    def update_dividend_reduction_rates(self, year: int, month: int, data: List[Dict]) -> int:
        """配当還元率データを更新"""
        # 既存データを削除
        self.execute_query(
            "DELETE FROM dividend_reduction_rates WHERE year = %s AND month = %s",
            (year, month)
        )
        
        # 新しいデータを挿入
        return self.insert_dividend_reduction_rates(data)
    
    # 会社規模判定基準データ関連
    def get_company_size_criteria(self, year: int = None, month: int = None) -> List[Dict]:
        """会社規模判定基準データを取得"""
        if year and month:
            query = """
                SELECT * FROM company_size_criteria
                WHERE year = %s AND month = %s
                ORDER BY industry_type, size_category
            """
            return self.execute_query(query, (year, month))
        else:
            query = """
                SELECT * FROM company_size_criteria
                ORDER BY year DESC, month DESC, industry_type, size_category
            """
            return self.execute_query(query)
    
    def insert_company_size_criteria(self, data: List[Dict]) -> int:
        """会社規模判定基準データを一括挿入"""
        inserted_count = 0
        
        for record in data:
            try:
                self.insert_record('company_size_criteria', record)
                inserted_count += 1
            except Exception as e:
                self.logger.error(f"Error inserting company size criteria: {e}")
        
        return inserted_count
    
    def update_company_size_criteria(self, year: int, month: int, data: List[Dict]) -> int:
        """会社規模判定基準データを更新"""
        # 既存データを削除
        self.execute_query(
            "DELETE FROM company_size_criteria WHERE year = %s AND month = %s",
            (year, month)
        )
        
        # 新しいデータを挿入
        return self.insert_company_size_criteria(data)
    
    # 更新履歴関連
    def get_update_history(self, limit: int = 50) -> List[Dict]:
        """更新履歴を取得"""
        query = """
            SELECT * FROM update_history
            ORDER BY check_date DESC
            LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    def insert_update_history(self, data: Dict) -> int:
        """更新履歴を挿入"""
        return self.insert_record('update_history', data)
    
    def get_latest_update(self, data_type: str = None) -> Optional[Dict]:
        """最新の更新履歴を取得"""
        if data_type:
            query = """
                SELECT * FROM update_history
                WHERE data_type = %s
                ORDER BY check_date DESC
                LIMIT 1
            """
            return self.execute_single_query(query, (data_type,))
        else:
            query = """
                SELECT * FROM update_history
                ORDER BY check_date DESC
                LIMIT 1
            """
            return self.execute_single_query(query)
    
    # システム設定関連
    def get_system_setting(self, key: str) -> Optional[str]:
        """システム設定を取得"""
        query = "SELECT setting_value FROM system_settings WHERE setting_key = %s"
        result = self.execute_single_query(query, (key,))
        return result['setting_value'] if result else None
    
    def set_system_setting(self, key: str, value: str, description: str = None) -> bool:
        """システム設定を更新"""
        data = {
            'setting_key': key,
            'setting_value': value,
            'description': description or f'Setting for {key}'
        }
        
        # UPSERT処理
        query = """
            INSERT INTO system_settings (setting_key, setting_value, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (setting_key)
            DO UPDATE SET
                setting_value = EXCLUDED.setting_value,
                description = EXCLUDED.description,
                updated_at = CURRENT_TIMESTAMP
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (key, value, description))
                conn.commit()
                return True
    
    # 統計情報
    def get_database_stats(self) -> Dict[str, Any]:
        """データベース統計情報を取得"""
        stats = {}
        
        # 各テーブルのレコード数
        tables = [
            'comparable_industry_data',
            'dividend_reduction_rates',
            'company_size_criteria',
            'update_history',
            'system_settings'
        ]
        
        for table in tables:
            query = f"SELECT COUNT(*) as count FROM {table}"
            result = self.execute_single_query(query)
            stats[f'{table}_count'] = result['count'] if result else 0
        
        # 最新の更新日時
        latest_update = self.get_latest_update()
        stats['last_update'] = latest_update['check_date'].isoformat() if latest_update else None
        
        # データの鮮度（最新データの年月）
        query = """
            SELECT MAX(year) as max_year, MAX(month) as max_month
            FROM comparable_industry_data
        """
        result = self.execute_single_query(query)
        if result:
            stats['latest_data_year'] = result['max_year']
            stats['latest_data_month'] = result['max_month']
        
        return stats
    
    # データベースの健全性チェック
    def health_check(self) -> Dict[str, Any]:
        """データベースの健全性をチェック"""
        health = {
            'status': 'healthy',
            'checks': {},
            'errors': []
        }
        
        try:
            # 接続テスト
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    health['checks']['connection'] = 'ok'
        except Exception as e:
            health['checks']['connection'] = 'failed'
            health['errors'].append(f"Connection failed: {str(e)}")
            health['status'] = 'unhealthy'
        
        try:
            # テーブル存在チェック
            tables = [
                'comparable_industry_data',
                'dividend_reduction_rates',
                'company_size_criteria',
                'update_history',
                'system_settings'
            ]
            
            for table in tables:
                query = f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
                result = self.execute_single_query(query)
                health['checks'][f'table_{table}'] = 'ok' if result and result['exists'] else 'missing'
                
                if not (result and result['exists']):
                    health['errors'].append(f"Table {table} is missing")
                    health['status'] = 'unhealthy'
        except Exception as e:
            health['checks']['table_check'] = 'failed'
            health['errors'].append(f"Table check failed: {str(e)}")
            health['status'] = 'unhealthy'
        
        return health 
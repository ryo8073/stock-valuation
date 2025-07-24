#!/usr/bin/env python3
"""
国税庁データバックアップスクリプト
GitHub Actionsで実行されるバックアップ処理
"""

import os
import json
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

def backup_current_data():
    """現在のデータベースからデータをバックアップ"""
    db_path = os.getenv('DATABASE_PATH', 'backend/data/stock_valuator.db')
    
    # SQLiteデータベースからデータを取得
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 会社規模判定基準データを取得
            cursor.execute("SELECT * FROM company_size_criteria")
            criteria_data = [dict(row) for row in cursor.fetchall()]
            
            # 類似業種比準価額データを取得
            cursor.execute("SELECT * FROM comparable_industry_data")
            industry_data = [dict(row) for row in cursor.fetchall()]
            
            # 配当還元率データを取得
            cursor.execute("SELECT * FROM dividend_reduction_rates")
            dividend_data = [dict(row) for row in cursor.fetchall()]
    else:
        # データベースが存在しない場合のデフォルト値
        criteria_data = []
        industry_data = []
        dividend_data = []
    
    # バックアップデータの構造化
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'criteria_data': criteria_data,
        'industry_data': industry_data,
        'dividend_data': dividend_data,
        'backup_source': 'sqlite_database'
    }
    
    # バックアップディレクトリの作成
    backup_dir = Path('data/backups')
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # バックアップファイルの保存
    backup_file = backup_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"Backup created: {backup_file}")
    return backup_file

def verify_primary_system():
    """プライマリシステム（Vercel）の動作確認"""
    health_check_url = os.getenv('VERCEL_HEALTH_CHECK_URL')
    
    if not health_check_url:
        print("Health check URL not configured")
        return False
    
    try:
        response = requests.get(health_check_url, timeout=30)
        if response.status_code == 200:
            print("Primary system (Vercel) is healthy")
            return True
        else:
            print(f"Primary system unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"Primary system check failed: {e}")
        return False

def check_data_freshness():
    """データの鮮度をチェック"""
    db_path = os.getenv('DATABASE_PATH', 'backend/data/stock_valuator.db')
    
    if not os.path.exists(db_path):
        print("Database not found")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 最新の更新日時を取得
            cursor.execute("""
                SELECT MAX(created_at) as last_update 
                FROM (
                    SELECT created_at FROM company_size_criteria
                    UNION ALL
                    SELECT created_at FROM comparable_industry_data
                    UNION ALL
                    SELECT created_at FROM dividend_reduction_rates
                )
            """)
            
            result = cursor.fetchone()
            if result and result[0]:
                last_update = datetime.fromisoformat(result[0])
                days_since_update = (datetime.now() - last_update).days
                
                print(f"Last data update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Days since last update: {days_since_update}")
                
                if days_since_update > 30:
                    print("WARNING: Data is more than 30 days old")
                    return False
                else:
                    print("Data freshness check passed")
                    return True
            else:
                print("No data found in database")
                return False
                
    except Exception as e:
        print(f"Data freshness check failed: {e}")
        return False

def send_notification(message, is_error=False):
    """通知の送信"""
    webhook_url = os.getenv('NOTIFICATION_WEBHOOK')
    
    if not webhook_url:
        print("Notification webhook not configured")
        return
    
    try:
        payload = {
            'text': f"{'❌' if is_error else '✅'} {message}",
            'username': 'Stock Valuator Pro Backup',
            'icon_emoji': ':chart_with_upwards_trend:'
        }
        
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Notification sent successfully")
        else:
            print(f"Notification failed: {response.status_code}")
            
    except Exception as e:
        print(f"Notification error: {e}")

def main():
    """メイン関数"""
    print("Starting tax data backup process...")
    
    try:
        # 1. データのバックアップ
        backup_file = backup_current_data()
        
        # 2. プライマリシステムの動作確認
        system_healthy = verify_primary_system()
        
        # 3. データの鮮度チェック
        data_fresh = check_data_freshness()
        
        # 4. 結果の通知
        if system_healthy and data_fresh:
            message = f"Backup completed successfully. File: {backup_file.name}"
            send_notification(message, is_error=False)
            print("Backup process completed successfully")
        else:
            message = f"Backup completed with warnings. System healthy: {system_healthy}, Data fresh: {data_fresh}"
            send_notification(message, is_error=True)
            print("Backup process completed with warnings")
            
    except Exception as e:
        error_message = f"Backup process failed: {str(e)}"
        send_notification(error_message, is_error=True)
        print(f"Backup process failed: {e}")
        raise

if __name__ == "__main__":
    main() 
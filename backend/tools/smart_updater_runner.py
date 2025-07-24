#!/usr/bin/env python3
"""
インテリジェント更新システム実行スクリプト
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.tax_data_manager import TaxDataManager
from modules.smart_update_system import SmartUpdateSystem

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('smart_updater.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='インテリジェント国税庁データ更新システム')
    parser.add_argument('--mode', choices=['check', 'approve', 'status', 'history'], 
                       default='check', help='実行モード')
    parser.add_argument('--data-type', choices=['comparable', 'dividend', 'company_size', 'all'],
                       help='対象データタイプ')
    parser.add_argument('--admin-user', help='管理者ユーザー名')
    parser.add_argument('--db-path', default='tax_data.db', help='データベースファイルのパス')
    parser.add_argument('--interval', type=int, default=168, help='チェック間隔（時間）')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # データマネージャーの初期化
        data_manager = TaxDataManager(args.db_path)
        
        # 設定の準備
        config = {
            'check_interval_hours': args.interval,
            'notification_enabled': True,
            'auto_update': False
        }
        
        # スマート更新システムの初期化
        smart_system = SmartUpdateSystem(data_manager, config)
        
        if args.mode == 'check':
            logger.info("インテリジェント更新チェックを実行")
            results = smart_system.smart_check()
            
            if results:
                print("更新チェック結果:")
                for data_type, available in results.items():
                    status = "利用可能" if available else "不要"
                    print(f"  {data_type}: {status}")
            else:
                print("更新チェックに失敗しました")
                sys.exit(1)
                
        elif args.mode == 'approve':
            if not args.data_type or not args.admin_user:
                print("エラー: --data-type と --admin-user が必要です")
                sys.exit(1)
            
            logger.info(f"{args.data_type}の更新を承認: {args.admin_user}")
            success = smart_system.approve_update(args.data_type, args.admin_user)
            
            if success:
                print(f"{args.data_type}の更新が完了しました")
                sys.exit(0)
            else:
                print(f"{args.data_type}の更新に失敗しました")
                sys.exit(1)
                
        elif args.mode == 'status':
            logger.info("更新状況を取得")
            status = smart_system.get_update_status()
            
            print("更新状況:")
            for data_type, info in status.items():
                print(f"  {data_type}:")
                print(f"    利用可能: {info['update_available']}")
                print(f"    ステータス: {info['status']}")
                print(f"    承認済み: {info['admin_approved']}")
                print(f"    チェック日時: {info['check_date']}")
                if info['update_executed_at']:
                    print(f"    更新実行日時: {info['update_executed_at']}")
                print()
                
        elif args.mode == 'history':
            logger.info("更新履歴を取得")
            history = smart_system.get_update_history(args.data_type, 10)
            
            print("更新履歴:")
            for record in history:
                print(f"  ID: {record['id']}")
                print(f"  データタイプ: {record['data_type']}")
                print(f"  チェック日時: {record['check_date']}")
                print(f"  更新利用可能: {record['update_available']}")
                print(f"  ステータス: {record['update_status']}")
                print(f"  承認済み: {record['admin_approved']}")
                print()
                
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
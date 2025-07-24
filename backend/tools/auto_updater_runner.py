#!/usr/bin/env python3
"""
国税庁データ自動更新システム実行スクリプト
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.tax_data_manager import TaxDataManager
from modules.tax_data_auto_updater import TaxDataAutoUpdater

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('auto_updater.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='国税庁データ自動更新システム')
    parser.add_argument('--mode', choices=['daemon', 'manual', 'check'], 
                       default='manual', help='実行モード')
    parser.add_argument('--config', help='設定ファイルのパス')
    parser.add_argument('--db-path', default='tax_data.db', help='データベースファイルのパス')
    parser.add_argument('--check-interval', type=int, default=24, 
                       help='チェック間隔（時間）')
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # データマネージャーの初期化
        data_manager = TaxDataManager(args.db_path)
        
        # 設定の準備
        config = {
            'check_interval_hours': args.check_interval
        }
        
        # 自動更新システムの初期化
        updater = TaxDataAutoUpdater(data_manager, config)
        
        if args.mode == 'daemon':
            logger.info("デーモンモードで自動更新システムを開始")
            updater.start_scheduler()
            
        elif args.mode == 'manual':
            logger.info("手動更新を実行")
            success = updater.manual_update()
            if success:
                logger.info("手動更新が完了しました")
                sys.exit(0)
            else:
                logger.error("手動更新に失敗しました")
                sys.exit(1)
                
        elif args.mode == 'check':
            logger.info("更新チェックを実行")
            has_updates = updater.check_for_updates()
            if has_updates:
                logger.info("更新が利用可能です")
                sys.exit(0)
            else:
                logger.info("更新はありません")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
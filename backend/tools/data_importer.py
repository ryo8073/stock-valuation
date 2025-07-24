#!/usr/bin/env python3
"""
国税庁データインポートツール
国税庁から提供される類似業種比準価額等のデータを自動でインポートするツール
"""

import argparse
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.tax_data_manager import TaxDataManager

def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data_import.log'),
            logging.StreamHandler()
        ]
    )

def import_comparable_industry_data(data_manager: TaxDataManager, file_path: str, year: int, month: int):
    """類似業種比準価額データのインポート"""
    if not os.path.exists(file_path):
        logging.error(f"ファイルが見つかりません: {file_path}")
        return False
    
    logging.info(f"類似業種比準価額データをインポート中: {file_path}")
    success = data_manager.import_comparable_industry_data(file_path, year, month)
    
    if success:
        logging.info(f"類似業種比準価額データのインポートが完了しました: {year}年{month}月")
    else:
        logging.error(f"類似業種比準価額データのインポートに失敗しました: {year}年{month}月")
    
    return success

def import_dividend_reduction_rates(data_manager: TaxDataManager, file_path: str, year: int, month: int):
    """配当還元率データのインポート"""
    if not os.path.exists(file_path):
        logging.error(f"ファイルが見つかりません: {file_path}")
        return False
    
    logging.info(f"配当還元率データをインポート中: {file_path}")
    success = data_manager.import_dividend_reduction_rates(file_path, year, month)
    
    if success:
        logging.info(f"配当還元率データのインポートが完了しました: {year}年{month}月")
    else:
        logging.error(f"配当還元率データのインポートに失敗しました: {year}年{month}月")
    
    return success

def import_company_size_criteria(data_manager: TaxDataManager, file_path: str, year: int, month: int):
    """会社規模判定基準データのインポート"""
    if not os.path.exists(file_path):
        logging.error(f"ファイルが見つかりません: {file_path}")
        return False
    
    logging.info(f"会社規模判定基準データをインポート中: {file_path}")
    success = data_manager.import_company_size_criteria(file_path, year, month)
    
    if success:
        logging.info(f"会社規模判定基準データのインポートが完了しました: {year}年{month}月")
    else:
        logging.error(f"会社規模判定基準データのインポートに失敗しました: {year}年{month}月")
    
    return success

def batch_import_from_directory(data_manager: TaxDataManager, data_dir: str, year: int, month: int):
    """ディレクトリから一括インポート"""
    data_dir_path = Path(data_dir)
    
    if not data_dir_path.exists():
        logging.error(f"ディレクトリが見つかりません: {data_dir}")
        return False
    
    success_count = 0
    total_count = 0
    
    # 類似業種比準価額データ
    comparable_file = data_dir_path / f"comparable_industry_{year}_{month:02d}.csv"
    if comparable_file.exists():
        total_count += 1
        if import_comparable_industry_data(data_manager, str(comparable_file), year, month):
            success_count += 1
    
    # 配当還元率データ
    dividend_file = data_dir_path / f"dividend_reduction_{year}_{month:02d}.csv"
    if dividend_file.exists():
        total_count += 1
        if import_dividend_reduction_rates(data_manager, str(dividend_file), year, month):
            success_count += 1
    
    # 会社規模判定基準データ
    size_file = data_dir_path / f"company_size_{year}_{month:02d}.csv"
    if size_file.exists():
        total_count += 1
        if import_company_size_criteria(data_manager, str(size_file), year, month):
            success_count += 1
    
    logging.info(f"一括インポート完了: {success_count}/{total_count}件成功")
    return success_count == total_count

def create_sample_csv_files(output_dir: str, year: int, month: int):
    """サンプルCSVファイルの作成"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 類似業種比準価額データのサンプル
    comparable_data = [
        "industry_code,industry_name,average_price,average_dividend,average_profit,average_net_assets",
        "01,製造業,500,10,80,300",
        "02,建設業,450,8,70,280",
        "03,卸売業,400,12,90,320",
        "04,小売業,350,15,60,250",
        "05,サービス業,600,20,100,400"
    ]
    
    comparable_file = output_path / f"comparable_industry_{year}_{month:02d}.csv"
    with open(comparable_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(comparable_data))
    
    # 配当還元率データのサンプル
    dividend_data = [
        "capital_range_min,capital_range_max,reduction_rate",
        "0,50000000,0.10",
        "50000000,100000000,0.12",
        "100000000,500000000,0.15",
        "500000000,1000000000,0.18",
        "1000000000,9999999999,0.20"
    ]
    
    dividend_file = output_path / f"dividend_reduction_{year}_{month:02d}.csv"
    with open(dividend_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(dividend_data))
    
    # 会社規模判定基準データのサンプル
    size_data = [
        "industry_type,size_category,employee_min,employee_max,asset_min,asset_max,sales_min,sales_max",
        "manufacturing,large,1000,999999,5000000000,999999999999,10000000000,999999999999",
        "manufacturing,medium,100,999,1000000000,4999999999,3000000000,9999999999",
        "manufacturing,small,0,99,0,999999999,0,2999999999",
        "wholesale,large,100,999999,1000000000,999999999999,30000000000,999999999999",
        "wholesale,medium,50,99,100000000,999999999,3000000000,29999999999",
        "wholesale,small,0,49,0,99999999,0,2999999999"
    ]
    
    size_file = output_path / f"company_size_{year}_{month:02d}.csv"
    with open(size_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(size_data))
    
    logging.info(f"サンプルCSVファイルを作成しました: {output_dir}")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='国税庁データインポートツール')
    parser.add_argument('--db-path', default='tax_data.db', help='データベースファイルのパス')
    parser.add_argument('--year', type=int, required=True, help='データの年')
    parser.add_argument('--month', type=int, required=True, help='データの月')
    parser.add_argument('--data-dir', help='データファイルのディレクトリ（一括インポート用）')
    parser.add_argument('--comparable-file', help='類似業種比準価額データファイルのパス')
    parser.add_argument('--dividend-file', help='配当還元率データファイルのパス')
    parser.add_argument('--size-file', help='会社規模判定基準データファイルのパス')
    parser.add_argument('--create-sample', action='store_true', help='サンプルCSVファイルを作成')
    parser.add_argument('--sample-output-dir', default='sample_data', help='サンプルファイルの出力ディレクトリ')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # データマネージャーの初期化
    data_manager = TaxDataManager(args.db_path)
    
    if args.create_sample:
        create_sample_csv_files(args.sample_output_dir, args.year, args.month)
        return
    
    success = True
    
    if args.data_dir:
        # ディレクトリから一括インポート
        success = batch_import_from_directory(data_manager, args.data_dir, args.year, args.month)
    else:
        # 個別ファイルインポート
        if args.comparable_file:
            success &= import_comparable_industry_data(data_manager, args.comparable_file, args.year, args.month)
        
        if args.dividend_file:
            success &= import_dividend_reduction_rates(data_manager, args.dividend_file, args.year, args.month)
        
        if args.size_file:
            success &= import_company_size_criteria(data_manager, args.size_file, args.year, args.month)
    
    if success:
        logging.info("データインポートが正常に完了しました")
        # 利用可能なデータ期間を表示
        periods = data_manager.get_available_data_periods()
        logging.info(f"利用可能なデータ期間: {periods}")
    else:
        logging.error("データインポートに失敗しました")
        sys.exit(1)

if __name__ == '__main__':
    main() 
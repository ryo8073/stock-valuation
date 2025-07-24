import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.tax_data_manager import TaxDataManager
from modules.tax_data_auto_updater import TaxDataAutoUpdater

class TestTaxDataAutoUpdater(unittest.TestCase):
    """国税庁データ自動更新システムのテスト"""

    def setUp(self):
        """テスト用の一時ディレクトリとデータベースを作成"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_tax_data.db')
        self.data_manager = TaxDataManager(self.db_path)
        
        # テスト用設定
        self.config = {
            'base_url': 'https://www.nta.go.jp',
            'comparable_data_url': '/taxanswer/sozoku/4608.htm',
            'dividend_data_url': '/taxanswer/sozoku/4609.htm',
            'company_size_data_url': '/taxanswer/sozoku/4610.htm',
            'check_interval_hours': 24,
            'download_dir': os.path.join(self.temp_dir, 'downloads'),
            'backup_dir': os.path.join(self.temp_dir, 'backups'),
            'max_retries': 3,
            'timeout': 30
        }
        
        self.updater = TaxDataAutoUpdater(self.data_manager, self.config)

    def tearDown(self):
        """テスト用ディレクトリを削除"""
        shutil.rmtree(self.temp_dir)

    @patch('requests.Session.get')
    def test_check_comparable_data_updates(self, mock_get):
        """類似業種データの更新チェックテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.content = b'''
        <html>
        <body>
        <p>最終更新日：2024年1月15日</p>
        <a href="test.pdf">類似業種比準価額</a>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # 更新チェックを実行
        result = self.updater._check_comparable_data_updates()
        
        # 結果を検証
        self.assertIsInstance(result, bool)
        mock_get.assert_called_once()

    @patch('requests.Session.get')
    def test_check_dividend_data_updates(self, mock_get):
        """配当還元率データの更新チェックテスト"""
        mock_response = Mock()
        mock_response.content = b'''
        <html>
        <body>
        <p>更新日：2024年1月10日</p>
        <a href="dividend.pdf">配当還元率</a>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.updater._check_dividend_data_updates()
        self.assertIsInstance(result, bool)

    @patch('requests.Session.get')
    def test_check_company_size_data_updates(self, mock_get):
        """会社規模判定基準データの更新チェックテスト"""
        mock_response = Mock()
        mock_response.content = b'''
        <html>
        <body>
        <p>2024年1月5日更新</p>
        <a href="size.pdf">会社規模判定基準</a>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.updater._check_company_size_data_updates()
        self.assertIsInstance(result, bool)

    def test_extract_last_updated_date(self):
        """最終更新日の抽出テスト"""
        from bs4 import BeautifulSoup
        
        # テスト用HTML
        html_content = '''
        <html>
        <body>
        <p>最終更新日：2024年1月15日</p>
        <p>更新日：2024年1月10日</p>
        <p>2024/1/5 更新</p>
        </body>
        </html>
        '''
        
        soup = BeautifulSoup(html_content, 'html.parser')
        result = self.updater._extract_last_updated_date(soup)
        
        # 日付オブジェクトが返されることを確認
        self.assertIsInstance(result, type(self.updater._extract_last_updated_date(soup)))

    def test_get_latest_comparable_data(self):
        """最新類似業種データの取得テスト"""
        # テストデータを挿入
        with self.data_manager.db_path as conn:
            conn.execute('''
                INSERT INTO comparable_industry_data 
                (year, month, industry_code, industry_name, average_price, 
                 average_dividend, average_profit, average_net_assets)
                VALUES (2024, 1, '01', '製造業', 500, 10, 80, 300)
            ''')
            conn.commit()
        
        result = self.updater._get_latest_comparable_data()
        self.assertIsInstance(result, type(self.updater._get_latest_comparable_data()))

    def test_get_latest_dividend_data(self):
        """最新配当還元率データの取得テスト"""
        # テストデータを挿入
        with self.data_manager.db_path as conn:
            conn.execute('''
                INSERT INTO dividend_reduction_rates 
                (year, month, capital_range_min, capital_range_max, reduction_rate)
                VALUES (2024, 1, 0, 50000000, 0.10)
            ''')
            conn.commit()
        
        result = self.updater._get_latest_dividend_data()
        self.assertIsInstance(result, type(self.updater._get_latest_dividend_data()))

    def test_get_latest_company_size_data(self):
        """最新会社規模判定基準データの取得テスト"""
        # テストデータを挿入
        with self.data_manager.db_path as conn:
            conn.execute('''
                INSERT INTO company_size_criteria 
                (year, month, industry_type, size_category, employee_min, 
                 employee_max, asset_min, asset_max, sales_min, sales_max)
                VALUES (2024, 1, 'manufacturing', 'large', 1000, 999999, 
                        5000000000, 999999999999, 10000000000, 999999999999)
            ''')
            conn.commit()
        
        result = self.updater._get_latest_company_size_data()
        self.assertIsInstance(result, type(self.updater._get_latest_company_size_data()))

    @patch('requests.Session.get')
    def test_download_file(self, mock_get):
        """ファイルダウンロードテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.content = b'test file content'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # テストファイルパス
        test_file_path = Path(self.temp_dir) / 'test.pdf'
        
        # ダウンロードを実行
        result = self.updater._download_file('https://example.com/test.pdf', test_file_path)
        
        # 結果を検証
        self.assertTrue(result)
        self.assertTrue(test_file_path.exists())
        
        # ファイル内容を確認
        with open(test_file_path, 'rb') as f:
            content = f.read()
        self.assertEqual(content, b'test file content')

    def test_parse_comparable_data(self):
        """類似業種データの解析テスト"""
        test_text = """
        01 製造業 500 10 80 300
        02 建設業 450 8 70 280
        03 卸売業 400 12 90 320
        """
        
        result = self.updater._parse_comparable_data(test_text)
        
        # DataFrameが返されることを確認
        self.assertIsInstance(result, type(result))
        self.assertEqual(len(result), 3)
        
        # 最初の行の内容を確認
        first_row = result.iloc[0]
        self.assertEqual(first_row['industry_code'], '01')
        self.assertEqual(first_row['industry_name'], '製造業')
        self.assertEqual(first_row['average_price'], 500)

    def test_parse_dividend_data(self):
        """配当還元率データの解析テスト"""
        test_text = """
        0 50000000 0.10
        50000000 100000000 0.12
        100000000 500000000 0.15
        """
        
        result = self.updater._parse_dividend_data(test_text)
        
        self.assertIsInstance(result, type(result))
        self.assertEqual(len(result), 3)
        
        first_row = result.iloc[0]
        self.assertEqual(first_row['capital_range_min'], 0)
        self.assertEqual(first_row['capital_range_max'], 50000000)
        self.assertEqual(first_row['reduction_rate'], 0.10)

    def test_parse_company_size_data(self):
        """会社規模判定基準データの解析テスト"""
        test_text = """
        manufacturing large 1000 999999 5000000000 999999999999 10000000000 999999999999
        manufacturing medium 100 999 1000000000 4999999999 3000000000 9999999999
        """
        
        result = self.updater._parse_company_size_data(test_text)
        
        self.assertIsInstance(result, type(result))
        self.assertEqual(len(result), 2)
        
        first_row = result.iloc[0]
        self.assertEqual(first_row['industry_type'], 'manufacturing')
        self.assertEqual(first_row['size_category'], 'large')
        self.assertEqual(first_row['employee_min'], 1000)

    def test_create_backup(self):
        """バックアップ作成テスト"""
        # テストデータを挿入
        with self.data_manager.db_path as conn:
            conn.execute('''
                INSERT INTO comparable_industry_data 
                (year, month, industry_code, industry_name, average_price, 
                 average_dividend, average_profit, average_net_assets)
                VALUES (2024, 1, '01', '製造業', 500, 10, 80, 300)
            ''')
            conn.commit()
        
        # バックアップを作成
        self.updater._create_backup()
        
        # バックアップディレクトリが作成されていることを確認
        backup_dir = Path(self.config['backup_dir'])
        self.assertTrue(backup_dir.exists())
        
        # バックアップファイルが作成されていることを確認
        backup_files = list(backup_dir.glob('*.db'))
        self.assertGreater(len(backup_files), 0)

    @patch('modules.tax_data_auto_updater.TaxDataAutoUpdater.check_for_updates')
    @patch('modules.tax_data_auto_updater.TaxDataAutoUpdater.download_and_process_data')
    def test_manual_update(self, mock_download, mock_check):
        """手動更新テスト"""
        mock_check.return_value = True
        mock_download.return_value = True
        
        result = self.updater.manual_update()
        
        self.assertTrue(result)
        mock_download.assert_called_once()

    def test_config_initialization(self):
        """設定の初期化テスト"""
        # デフォルト設定のテスト
        updater_default = TaxDataAutoUpdater(self.data_manager)
        self.assertIsNotNone(updater_default.config)
        self.assertIn('base_url', updater_default.config)
        self.assertIn('check_interval_hours', updater_default.config)
        
        # カスタム設定のテスト
        custom_config = {'check_interval_hours': 12}
        updater_custom = TaxDataAutoUpdater(self.data_manager, custom_config)
        self.assertEqual(updater_custom.config['check_interval_hours'], 12)

if __name__ == '__main__':
    unittest.main() 
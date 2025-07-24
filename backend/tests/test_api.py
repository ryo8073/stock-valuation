import unittest
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

class TestAPIEndpoints(unittest.TestCase):
    """APIエンドポイントの品質保証テスト"""

    def setUp(self):
        """テスト用アプリケーションの初期化"""
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        self.valid_data = {
            'is_family_shareholder': True,
            'shares_outstanding': 1000,
            'company_size': {
                'employees': 50,
                'assets': 500000000,
                'sales': 1000000000,
            },
            'net_asset': {
                'assets': 1000000000,
                'liabilities': 500000000,
                'unrealized_gains': 200000000,
            },
            'comparable': {
                'dividend': 15,
                'profit': 100,
                'net_assets': 400,
            },
            'dividend_reduction': {
                'dividend1': 10,
                'dividend2': 12,
                'capital': 50000000,
            },
        }

    def test_evaluate_endpoint_success(self):
        """正常な評価リクエストのテスト"""
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('evaluation_method', data)
        self.assertIn('value_per_share', data)
        self.assertIn('details', data)
        self.assertGreater(data['value_per_share'], 0)

    def test_evaluate_endpoint_invalid_json(self):
        """不正なJSONデータのテスト"""
        response = self.client.post(
            '/api/evaluate',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_evaluate_endpoint_empty_data(self):
        """空データのテスト"""
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)  # 空データでも計算可能
        data = json.loads(response.data)
        self.assertIn('value_per_share', data)

    def test_evaluate_endpoint_missing_content_type(self):
        """Content-Typeが指定されていない場合のテスト"""
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps(self.valid_data)
        )
        
        self.assertEqual(response.status_code, 400)

    def test_evaluate_endpoint_dividend_method(self):
        """配当還元方式のテスト"""
        data = self.valid_data.copy()
        data['is_family_shareholder'] = False
        
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result['evaluation_method'], "特例的評価方式（配当還元方式）")

    def test_evaluate_endpoint_large_numbers(self):
        """大きな数値のテスト"""
        data = self.valid_data.copy()
        data['company_size']['assets'] = 1000000000000  # 1兆円
        data['company_size']['sales'] = 2000000000000   # 2兆円
        
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertGreater(result['value_per_share'], 0)

    def test_evaluate_endpoint_negative_values(self):
        """負の値のテスト"""
        data = self.valid_data.copy()
        data['net_asset']['liabilities'] = -100000000  # 負の負債
        
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertIsInstance(result['value_per_share'], (int, float))

    def test_evaluate_endpoint_zero_shares(self):
        """株式数が0の場合のテスト"""
        data = self.valid_data.copy()
        data['shares_outstanding'] = 0
        
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertEqual(result['value_per_share'], 0)

    def test_cors_headers(self):
        """CORSヘッダーのテスト"""
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        # CORSヘッダーが設定されていることを確認
        self.assertIn('Access-Control-Allow-Origin', response.headers)

    def test_response_time(self):
        """レスポンス時間のテスト"""
        import time
        start_time = time.time()
        
        response = self.client.post(
            '/api/evaluate',
            data=json.dumps(self.valid_data),
            content_type='application/json'
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0)  # 1秒以内にレスポンス

if __name__ == '__main__':
    unittest.main() 
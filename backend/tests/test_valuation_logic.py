import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.valuation_logic import (
    judge_company_size,
    calculate_net_asset_value,
    calculate_comparable_industry_value,
    calculate_dividend_reduction_value,
    evaluate_stock
)

class TestValuationLogic(unittest.TestCase):
    """非上場株式評価ロジックの品質保証テスト"""

    def setUp(self):
        """テストデータの初期化"""
        self.sample_data = {
            'is_family_shareholder': True,
            'shares_outstanding': 1000,
            'company_size': {
                'employees': 50,
                'assets': 500000000,  # 5億円
                'sales': 1000000000,  # 10億円
            },
            'net_asset': {
                'assets': 1000000000,  # 10億円
                'liabilities': 500000000,  # 5億円
                'unrealized_gains': 200000000,  # 2億円
            },
            'comparable': {
                'dividend': 15,
                'profit': 100,
                'net_assets': 400,
            },
            'dividend_reduction': {
                'dividend1': 10,
                'dividend2': 12,
                'capital': 50000000,  # 5千万円
            },
        }

    def test_judge_company_size(self):
        """会社規模判定ロジックのテスト"""
        # 大会社のテスト
        self.assertEqual(
            judge_company_size(100, 20000000000, 50000000000),  # 従業員100人、資産200億円、売上500億円
            "大会社"
        )
        
        # 小会社のテスト
        self.assertEqual(
            judge_company_size(10, 100000000, 200000000),  # 従業員10人、資産1億円、売上2億円
            "小会社"
        )
        
        # 中会社のテスト
        self.assertEqual(
            judge_company_size(50, 5000000000, 10000000000),  # 従業員50人、資産50億円、売上100億円
            "中会社"
        )

    def test_calculate_net_asset_value(self):
        """純資産価額方式の計算テスト"""
        data = {
            'shares_outstanding': 1000,
            'net_asset': {
                'assets': 1000000000,  # 10億円
                'liabilities': 500000000,  # 5億円
                'unrealized_gains': 200000000,  # 2億円
            }
        }
        
        result = calculate_net_asset_value(data)
        expected = (1000000000 - 500000000 - (200000000 * 0.37)) / 1000
        self.assertAlmostEqual(result, expected, places=0)

    def test_calculate_comparable_industry_value(self):
        """類似業種比準価額方式の計算テスト"""
        data = {
            'comparable': {
                'dividend': 15,
                'profit': 100,
                'net_assets': 400,
            }
        }
        
        result = calculate_comparable_industry_value(data)
        # 計算式: 500 * ((15/10 + 3*100/80 + 400/300) / 5) * 0.7
        self.assertGreater(result, 0)
        self.assertIsInstance(result, (int, float))

    def test_calculate_dividend_reduction_value(self):
        """配当還元方式の計算テスト"""
        data = {
            'shares_outstanding': 1000,
            'dividend_reduction': {
                'dividend1': 10,
                'dividend2': 12,
                'capital': 50000000,  # 5千万円
            }
        }
        
        result = calculate_dividend_reduction_value(data)
        # 平均配当: (10+12)/2 = 11円
        # 1株当たり資本金: 50000000/1000 = 50000円
        # 資本金比率: 50000/50 = 1000
        # 評価額: (11/0.10) * 1000 = 110000円
        expected = (11 / 0.10) * 1000
        self.assertAlmostEqual(result, expected, places=0)

    def test_evaluate_stock_principle_method(self):
        """原則的評価方式の統合テスト"""
        result = evaluate_stock(self.sample_data)
        
        self.assertIn('evaluation_method', result)
        self.assertIn('value_per_share', result)
        self.assertIn('details', result)
        self.assertGreater(result['value_per_share'], 0)
        self.assertIsInstance(result['value_per_share'], (int, float))

    def test_evaluate_stock_dividend_method(self):
        """配当還元方式の統合テスト"""
        data = self.sample_data.copy()
        data['is_family_shareholder'] = False
        
        result = evaluate_stock(data)
        
        self.assertEqual(result['evaluation_method'], "特例的評価方式（配当還元方式）")
        self.assertGreater(result['value_per_share'], 0)

    def test_edge_cases(self):
        """エッジケースのテスト"""
        # 株式数が0の場合
        data = self.sample_data.copy()
        data['shares_outstanding'] = 0
        result = evaluate_stock(data)
        self.assertEqual(result['value_per_share'], 0)
        
        # 負債が資産を上回る場合
        data = self.sample_data.copy()
        data['net_asset']['liabilities'] = 2000000000  # 20億円
        result = evaluate_stock(data)
        self.assertLess(result['value_per_share'], 0)

    def test_data_validation(self):
        """データ検証のテスト"""
        # 必須データが不足している場合
        incomplete_data = {'shares_outstanding': 1000}
        result = evaluate_stock(incomplete_data)
        self.assertIsInstance(result['value_per_share'], (int, float))

    def test_calculation_consistency(self):
        """計算の一貫性テスト"""
        # 同じデータで複数回計算しても同じ結果になることを確認
        result1 = evaluate_stock(self.sample_data)
        result2 = evaluate_stock(self.sample_data)
        
        self.assertEqual(result1['value_per_share'], result2['value_per_share'])
        self.assertEqual(result1['evaluation_method'], result2['evaluation_method'])

if __name__ == '__main__':
    unittest.main() 
import math
from datetime import date
from typing import Dict, Optional
from .tax_data_manager import TaxDataManager

class ValuationLogicV2:
    """データベース対応版の非上場株式評価ロジック"""
    
    def __init__(self, data_manager: TaxDataManager):
        self.data_manager = data_manager
    
    def judge_company_size(self, employee_count: int, total_assets: int, sales_amount: int, 
                          industry_type: str, target_date: date) -> str:
        """
        会社の規模（大・中・小）を判定する（データベース基準版）
        
        Args:
            employee_count: 従業員数
            total_assets: 総資産価額
            sales_amount: 売上金額
            industry_type: 業種タイプ
            target_date: 対象日
            
        Returns:
            str: 会社規模（"大会社", "中会社", "小会社"）
        """
        criteria = self.data_manager.get_company_size_criteria(industry_type, target_date)
        
        if not criteria:
            # データベースにデータがない場合はデフォルトロジックを使用
            return self._judge_company_size_default(employee_count, total_assets, sales_amount)
        
        # 大会社の判定
        if 'large' in criteria:
            large_criteria = criteria['large']
            if (large_criteria['employee_min'] <= employee_count <= large_criteria['employee_max'] or
                (large_criteria['asset_min'] <= total_assets <= large_criteria['asset_max'] and
                 large_criteria['sales_min'] <= sales_amount <= large_criteria['sales_max'])):
                return "大会社"
        
        # 小会社の判定
        if 'small' in criteria:
            small_criteria = criteria['small']
            if (small_criteria['employee_min'] <= employee_count <= small_criteria['employee_max'] or
                (small_criteria['asset_min'] <= total_assets <= small_criteria['asset_max'] and
                 small_criteria['sales_min'] <= sales_amount <= small_criteria['sales_max'])):
                return "小会社"
        
        # 上記以外は中会社
        return "中会社"
    
    def _judge_company_size_default(self, employee_count: int, total_assets: int, sales_amount: int) -> str:
        """デフォルトの会社規模判定ロジック"""
        # 従業員基準
        is_employee_L = employee_count >= 35
        # 資産・売上基準
        is_asset_L = total_assets >= 15 * 100000000  # 15億円
        is_asset_S = total_assets < 2 * 100000000    # 2億円
        is_sales_L = sales_amount >= 30 * 100000000  # 30億円
        is_sales_S = sales_amount < 3 * 100000000    # 3億円
        
        if is_employee_L or (is_asset_L and is_sales_L):
            return "大会社"
        if is_asset_S and is_sales_S:
            return "小会社"
        return "中会社"
    
    def calculate_net_asset_value(self, data: Dict) -> float:
        """純資産価額方式の計算"""
        net_asset_info = data.get('net_asset', {})
        assets = net_asset_info.get('assets', 0)
        liabilities = net_asset_info.get('liabilities', 0)
        unrealized_gains = net_asset_info.get('unrealized_gains', 0)
        shares = data.get('shares_outstanding', 1)
        
        # 評価差額に対する法人税等相当額(37%)を控除
        tax_on_gains = unrealized_gains * 0.37
        net_assets = assets - liabilities - tax_on_gains
        
        value_per_share = net_assets / shares if shares > 0 else 0
        return value_per_share
    
    def calculate_comparable_industry_value(self, data: Dict, industry_code: str, 
                                          target_date: date) -> float:
        """類似業種比準価額方式の計算（データベース版）"""
        comparable_info = data.get('comparable', {})
        
        # データベースから類似業種データを取得
        comparable_data = self.data_manager.get_comparable_industry_data(industry_code, target_date)
        
        if not comparable_data:
            # データベースにデータがない場合はデフォルトデータを使用
            comparable_data = {'price': 500, 'dividend': 10, 'profit': 80, 'net_assets': 300}
        
        company_dividend = comparable_info.get('dividend', 0)
        company_profit = comparable_info.get('profit', 0)
        company_net_assets = comparable_info.get('net_assets', 0)
        
        # 各比率を計算
        dividend_ratio = company_dividend / comparable_data['dividend'] if comparable_data['dividend'] > 0 else 0
        profit_ratio = company_profit / comparable_data['profit'] if comparable_data['profit'] > 0 else 0
        net_assets_ratio = company_net_assets / comparable_data['net_assets'] if comparable_data['net_assets'] > 0 else 0
        
        # 比率の平均を計算（利益は3倍のウェイト）
        average_ratio = (dividend_ratio + (profit_ratio * 3) + net_assets_ratio) / 5
        
        # 大会社の斟酌率0.7を適用
        return comparable_data['price'] * average_ratio * 0.7
    
    def calculate_dividend_reduction_value(self, data: Dict, target_date: date) -> float:
        """配当還元方式の計算（データベース版）"""
        dividend_info = data.get('dividend_reduction', {})
        shares = data.get('shares_outstanding', 1)
        
        if shares <= 0:
            return 0
        
        # 過去2年間の平均配当
        avg_dividend = (dividend_info.get('dividend1', 0) + dividend_info.get('dividend2', 0)) / 2
        
        # 1株当たりの資本金等の額
        capital_per_share = dividend_info.get('capital', 0) / shares
        
        # データベースから配当還元率を取得
        reduction_rate = self.data_manager.get_dividend_reduction_rate(
            int(capital_per_share), target_date
        )
        
        # 配当還元価額の計算式
        value_per_share = (avg_dividend / reduction_rate) * (capital_per_share / 50)
        return value_per_share
    
    def evaluate_stock(self, data: Dict, industry_code: str = "01", 
                      industry_type: str = "manufacturing", 
                      target_date: Optional[date] = None) -> Dict:
        """
        評価ロジックのメインコントローラー（データベース対応版）
        
        Args:
            data: 評価データ
            industry_code: 業種コード
            industry_type: 業種タイプ
            target_date: 対象日（Noneの場合は現在日）
            
        Returns:
            Dict: 評価結果
        """
        if target_date is None:
            target_date = date.today()
        
        result = {"evaluation_method": "", "value_per_share": 0, "details": {}}
        
        if not data.get('is_family_shareholder', True):
            # 特例的評価方式
            result['evaluation_method'] = "特例的評価方式（配当還元方式）"
            result['value_per_share'] = self.calculate_dividend_reduction_value(data, target_date)
            result['details']['target_date'] = target_date.isoformat()
            return result
        
        # --- 以下、原則的評価方式 ---
        size_info = data.get('company_size', {})
        company_size = self.judge_company_size(
            size_info.get('employees', 0),
            size_info.get('assets', 0),
            size_info.get('sales', 0),
            industry_type,
            target_date
        )
        result['details']['company_size'] = company_size
        result['details']['target_date'] = target_date.isoformat()
        result['details']['industry_code'] = industry_code
        result['details']['industry_type'] = industry_type
        
        # 評価額を事前に計算
        net_asset_value = self.calculate_net_asset_value(data)
        comparable_value = self.calculate_comparable_industry_value(data, industry_code, target_date)
        result['details']['net_asset_value'] = net_asset_value
        result['details']['comparable_value'] = comparable_value
        
        if company_size == "小会社":
            result['evaluation_method'] = "純資産価額方式"
            result['value_per_share'] = net_asset_value
            
        elif company_size == "大会社":
            result['evaluation_method'] = "類似業種比準価額方式"
            result['value_per_share'] = min(comparable_value, net_asset_value)  # 有利選択
            result['details']['note'] = "類似業種比準価額方式と純資産価額方式のうち、低い方の価額を選択しています。"
            
        elif company_size == "中会社":
            result['evaluation_method'] = "併用方式"
            l_ratio = 0.75  # Lの割合を仮定（本来は規模により変動）
            result['details']['l_ratio'] = l_ratio
            
            combined_value = (comparable_value * l_ratio) + (net_asset_value * (1 - l_ratio))
            result['details']['combined_value'] = combined_value
            
            result['value_per_share'] = min(combined_value, net_asset_value)  # 有利選択
            result['details']['note'] = "併用方式による価額と純資産価額のうち、低い方の価額を選択しています。"
        
        # 最終価額を整数に丸める
        result['value_per_share'] = math.ceil(result['value_per_share']) if result['value_per_share'] is not None else 0
        return result 
import math

# --- 判定ロジック ---
def judge_company_size(employee_count, total_assets, sales_amount):
    """
    会社の規模（大・中・小）を判定する。
    実際のロジックは業種ごとに異なるが、ここでは「卸売業」を仮定。
    """
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
    # 上記以外は中会社（詳細判定は省略し、一律「中会社」とする）
    return "中会社"

# --- 計算ロジック ---
def calculate_net_asset_value(data):
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

def calculate_comparable_industry_value(data):
    """類似業種比準価額方式の計算"""
    comparable_info = data.get('comparable', {})
    # 類似業種のデータ（本来はDBから取得、ここでは仮データ）
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

def calculate_dividend_reduction_value(data):
    """配当還元方式の計算"""
    dividend_info = data.get('dividend_reduction', {})
    shares = data.get('shares_outstanding', 1)
    if shares <= 0: 
        return 0
    
    # 過去2年間の平均配当
    avg_dividend = (dividend_info.get('dividend1', 0) + dividend_info.get('dividend2', 0)) / 2
    # 1株当たりの資本金等の額
    capital_per_share = dividend_info.get('capital', 0) / shares
    capital_ratio = capital_per_share / 50
    
    # 配当還元価額の計算式
    value_per_share = (avg_dividend / 0.10) * capital_ratio
    return value_per_share

# --- メインコントローラー ---
def evaluate_stock(data):
    """評価ロジックのメインコントローラー"""
    result = {"evaluation_method": "", "value_per_share": 0, "details": {}}
    
    if not data.get('is_family_shareholder', True):
        # 特例的評価方式
        result['evaluation_method'] = "特例的評価方式（配当還元方式）"
        result['value_per_share'] = calculate_dividend_reduction_value(data)
        return result
    
    # --- 以下、原則的評価方式 ---
    size_info = data.get('company_size', {})
    company_size = judge_company_size(
        size_info.get('employees', 0),
        size_info.get('assets', 0),
        size_info.get('sales', 0)
    )
    result['details']['company_size'] = company_size
    
    # 評価額を事前に計算
    net_asset_value = calculate_net_asset_value(data)
    comparable_value = calculate_comparable_industry_value(data)
    result['details']['net_asset_value'] = net_asset_value
    result['details']['comparable_value'] = comparable_value
    
    if company_size == "小会社":
        result['evaluation_method'] = "純資産価額方式"
        result['value_per_share'] = net_asset_value
        
    elif company_size == "大会社":
        result['evaluation_method'] = "類似業種比準価額方式"
        result['value_per_share'] = min(comparable_value, net_asset_value) # 有利選択
        result['details']['note'] = "類似業種比準価額方式と純資産価額方式のうち、低い方の価額を選択しています。"
        
    elif company_size == "中会社":
        result['evaluation_method'] = "併用方式"
        l_ratio = 0.75  # Lの割合を仮定（本来は規模により変動）
        result['details']['l_ratio'] = l_ratio
        
        combined_value = (comparable_value * l_ratio) + (net_asset_value * (1 - l_ratio))
        result['details']['combined_value'] = combined_value
        
        result['value_per_share'] = min(combined_value, net_asset_value) # 有利選択
        result['details']['note'] = "併用方式による価額と純資産価額のうち、低い方の価額を選択しています。"
    
    # 最終価額を整数に丸める
    result['value_per_share'] = math.ceil(result['value_per_share']) if result['value_per_share'] is not None else 0
    return result

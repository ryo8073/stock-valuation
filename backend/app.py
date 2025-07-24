from flask import Flask, request, jsonify
from flask_cors import CORS
from modules.valuation_logic import evaluate_stock
from modules.database_manager import DatabaseManager
from modules.tax_data_manager import TaxDataManager
import logging
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# データベースマネージャーの初期化
try:
    db_manager = DatabaseManager()
    tax_data_manager = TaxDataManager()
    logger.info("Database managers initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database managers: {e}")
    db_manager = None
    tax_data_manager = None

@app.route('/api/evaluate', methods=['POST'])
def evaluate():
    """
    フロントエンドから評価データを受け取り、評価額を計算して返すAPIエンドポイント
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input"}), 400
        
        # 評価ロジックモジュールを呼び出し
        result = evaluate_stock(data)
        
        return jsonify(result)
        
    except Exception as e:
        # エラー発生時は詳細をログに出力すると良い
        logger.error(f"Error during evaluation: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """ヘルスチェックエンドポイント"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }
    
    # データベースの健全性チェック
    if db_manager:
        try:
            db_health = db_manager.health_check()
            health_status['database'] = db_health
            if db_health['status'] != 'healthy':
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['database'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['status'] = 'unhealthy'
    else:
        health_status['database'] = {'status': 'unavailable'}
        health_status['status'] = 'degraded'
    
    return jsonify(health_status)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """データベース統計情報を取得"""
    if not db_manager:
        return jsonify({'error': 'Database manager not available'}), 503
    
    try:
        stats = db_manager.get_database_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f'Stats error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax-data/comparable', methods=['GET'])
def get_comparable_data():
    """類似業種比準価額データを取得"""
    if not db_manager:
        return jsonify({'error': 'Database manager not available'}), 503
    
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        data = db_manager.get_comparable_industry_data(year, month)
        return jsonify({'data': data})
    except Exception as e:
        logger.error(f'Comparable data error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax-data/dividend', methods=['GET'])
def get_dividend_data():
    """配当還元率データを取得"""
    if not db_manager:
        return jsonify({'error': 'Database manager not available'}), 503
    
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        data = db_manager.get_dividend_reduction_rates(year, month)
        return jsonify({'data': data})
    except Exception as e:
        logger.error(f'Dividend data error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax-data/company-size', methods=['GET'])
def get_company_size_data():
    """会社規模判定基準データを取得"""
    if not db_manager:
        return jsonify({'error': 'Database manager not available'}), 503
    
    try:
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        
        data = db_manager.get_company_size_criteria(year, month)
        return jsonify({'data': data})
    except Exception as e:
        logger.error(f'Company size data error: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-history', methods=['GET'])
def get_update_history():
    """更新履歴を取得"""
    if not db_manager:
        return jsonify({'error': 'Database manager not available'}), 503
    
    try:
        limit = request.args.get('limit', 50, type=int)
        data = db_manager.get_update_history(limit)
        return jsonify({'data': data})
    except Exception as e:
        logger.error(f'Update history error: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

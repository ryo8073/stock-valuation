# backend/admin_routes.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
import json
import sqlite3
from datetime import datetime
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 簡単な認証（本番では適切な認証システムを使用）
        stored_hash = os.getenv('ADMIN_PASSWORD_HASH', generate_password_hash('admin123'))
        
        if username == 'admin' and check_password_hash(stored_hash, password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('認証に失敗しました')
    
    return render_template('admin/login.html')

@admin_bp.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    
    # システム状態の取得
    system_status = get_system_status()
    recent_updates = get_recent_updates()
    
    return render_template('admin/dashboard.html', 
                         status=system_status, 
                         updates=recent_updates)

@admin_bp.route('/manual-update', methods=['GET', 'POST'])
def manual_update():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    
    if request.method == 'POST':
        try:
            # 手動データ更新の実行
            if 'data_file' in request.files:
                file = request.files['data_file']
                if file.filename.endswith('.json'):
                    data = json.load(file)
                    result = update_database_manual(data)
                    flash(f'データ更新完了: {result["updated_records"]}件')
                else:
                    flash('JSONファイルを選択してください')
            else:
                # 自動取得による更新
                result = trigger_manual_fetch()
                flash(f'自動取得完了: {result["status"]}')
                
        except Exception as e:
            flash(f'更新エラー: {str(e)}')
    
    return render_template('admin/manual_update.html')

@admin_bp.route('/system-logs')
def system_logs():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.login'))
    
    logs = get_system_logs(limit=100)
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/api/system-status')
def api_system_status():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    status = get_system_status()
    return jsonify(status)

@admin_bp.route('/api/trigger-update', methods=['POST'])
def api_trigger_update():
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        result = trigger_manual_fetch()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_system_status():
    """システムの現在状態を取得"""
    return {
        'last_update': get_last_update_time(),
        'total_records': get_total_record_count(),
        'system_health': check_system_health(),
        'next_scheduled_update': get_next_scheduled_time()
    }

def get_recent_updates():
    """最近の更新履歴を取得"""
    db_path = os.getenv('DATABASE_PATH', 'data/stock_valuator.db')
    
    if not os.path.exists(db_path):
        return []
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT created_at, data_type, update_status, record_count
                FROM update_history
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            return [dict(zip(['created_at', 'data_type', 'status', 'record_count'], row)) 
                   for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting recent updates: {e}")
        return []

def get_system_logs(limit=100):
    """システムログを取得"""
    log_files = [
        'backend/logs/app.log',
        'backend/logs/auto_updater.log',
        'backend/logs/smart_updater.log'
    ]
    
    logs = []
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()[-limit:]
                    logs.extend([{'file': log_file, 'line': line.strip()} for line in lines])
            except Exception as e:
                print(f"Error reading log file {log_file}: {e}")
    
    return sorted(logs, key=lambda x: x['line'], reverse=True)[:limit]

def update_database_manual(data):
    """手動でのデータベース更新"""
    db_path = os.getenv('DATABASE_PATH', 'data/stock_valuator.db')
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        updated_count = 0
        
        for record in data:
            # データの検証
            if validate_record(record):
                # 更新または挿入
                cursor.execute("""
                    INSERT OR REPLACE INTO company_size_criteria 
                    (industry_code, industry_name, large_employee, large_capital, large_sales)
                    VALUES (?, ?, ?, ?, ?)
                """, (record['industry_code'], record['industry_name'], 
                     record['large_employee'], record['large_capital'], record['large_sales']))
                updated_count += 1
        
        conn.commit()
        
        # 更新ログの記録
        log_manual_update(updated_count)
        
    return {'updated_records': updated_count}

def trigger_manual_fetch():
    """手動でのデータ取得をトリガー"""
    # Vercel関数を呼び出し
    import requests
    
    vercel_url = os.getenv('VERCEL_FUNCTION_URL')
    if not vercel_url:
        return {'status': 'error', 'message': 'Vercel function URL not configured'}
    
    try:
        response = requests.post(f"{vercel_url}/api/cron/update-tax-data", timeout=300)
        if response.status_code == 200:
            return {'status': 'success', 'data': response.json()}
        else:
            return {'status': 'error', 'message': f'HTTP {response.status_code}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_last_update_time():
    """最後の更新日時を取得"""
    db_path = os.getenv('DATABASE_PATH', 'data/stock_valuator.db')
    
    if not os.path.exists(db_path):
        return None
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(created_at) FROM update_history
            """)
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
    except Exception as e:
        print(f"Error getting last update time: {e}")
        return None

def get_total_record_count():
    """総レコード数を取得"""
    db_path = os.getenv('DATABASE_PATH', 'data/stock_valuator.db')
    
    if not os.path.exists(db_path):
        return 0
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM company_size_criteria) +
                    (SELECT COUNT(*) FROM comparable_industry_data) +
                    (SELECT COUNT(*) FROM dividend_reduction_rates)
            """)
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"Error getting total record count: {e}")
        return 0

def check_system_health():
    """システムの健全性をチェック"""
    # 簡略化されたヘルスチェック
    return {
        'database': check_database_health(),
        'api': check_api_health(),
        'overall': 'healthy'
    }

def check_database_health():
    """データベースの健全性をチェック"""
    db_path = os.getenv('DATABASE_PATH', 'data/stock_valuator.db')
    
    if not os.path.exists(db_path):
        return 'unhealthy'
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            return 'healthy' if result and result[0] == 'ok' else 'unhealthy'
    except Exception as e:
        print(f"Database health check failed: {e}")
        return 'unhealthy'

def check_api_health():
    """APIの健全性をチェック"""
    try:
        import requests
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        return 'healthy' if response.status_code == 200 else 'unhealthy'
    except Exception as e:
        print(f"API health check failed: {e}")
        return 'unhealthy'

def get_next_scheduled_time():
    """次回のスケジュール更新時刻を取得"""
    # 毎週月曜日午前2時（JST）
    from datetime import datetime, timedelta
    
    now = datetime.now()
    days_until_monday = (7 - now.weekday()) % 7
    next_monday = now + timedelta(days=days_until_monday)
    next_update = next_monday.replace(hour=2, minute=0, second=0, microsecond=0)
    
    return next_update.isoformat()

def validate_record(record):
    """レコードの検証"""
    required_fields = ['industry_code', 'industry_name']
    return all(field in record for field in required_fields)

def log_manual_update(updated_count):
    """手動更新のログ記録"""
    db_path = os.getenv('DATABASE_PATH', 'data/stock_valuator.db')
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO update_history 
                (data_type, update_status, record_count, created_at)
                VALUES (?, ?, ?, ?)
            """, ('manual_update', 'completed', updated_count, datetime.now().isoformat()))
            conn.commit()
    except Exception as e:
        print(f"Error logging manual update: {e}") 
# Stock Valuator Pro データ更新システム実装ガイド

**作成者**: Manus AI  
**作成日**: 2025年7月24日  
**対象**: 開発チーム  
**バージョン**: 1.0

## 概要

本ガイドは、技術分析レポートで推奨されたハイブリッドアプローチ（Vercel Cron Jobs + GitHub Actions + 管理画面）の具体的な実装方法を詳述します。

## 推奨実装アーキテクチャ

### 1. Vercel Cron Jobs（メインシステム）

**ファイル構成:**
```
api/
├── cron/
│   ├── update-tax-data.js
│   └── health-check.js
├── admin/
│   ├── manual-update.js
│   └── system-status.js
└── utils/
    ├── nta-scraper.js
    ├── data-validator.js
    └── notification.js
```

**メインの更新関数:**
```javascript
// api/cron/update-tax-data.js
import { fetchNTAData, validateData, updateDatabase, notifyUpdate } from '../utils';

export default async function handler(req, res) {
  // Cron jobからの実行のみ許可
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    console.log('Starting scheduled data update...');
    
    // 1. 国税庁サイトからデータ取得
    const latestData = await fetchNTAData();
    
    // 2. データ検証
    const validationResult = await validateData(latestData);
    if (!validationResult.isValid) {
      throw new Error(`Data validation failed: ${validationResult.errors.join(', ')}`);
    }
    
    // 3. 現在のデータと比較
    const currentData = await getCurrentData();
    const hasChanges = compareData(latestData, currentData);
    
    if (hasChanges) {
      // 4. データベース更新
      await updateDatabase(latestData);
      
      // 5. 更新通知
      await notifyUpdate({
        timestamp: new Date().toISOString(),
        changes: hasChanges,
        recordCount: latestData.length
      });
      
      console.log('Data update completed successfully');
      res.status(200).json({ 
        status: 'success', 
        message: 'Data updated',
        changes: hasChanges.length 
      });
    } else {
      console.log('No changes detected');
      res.status(200).json({ 
        status: 'success', 
        message: 'No changes detected' 
      });
    }
    
  } catch (error) {
    console.error('Data update failed:', error);
    
    // エラー通知
    await notifyError({
      error: error.message,
      timestamp: new Date().toISOString(),
      stack: error.stack
    });
    
    res.status(500).json({ 
      status: 'error', 
      message: error.message 
    });
  }
}
```

**Vercel設定ファイル:**
```json
// vercel.json
{
  "functions": {
    "api/cron/update-tax-data.js": {
      "maxDuration": 300
    }
  },
  "crons": [
    {
      "path": "/api/cron/update-tax-data",
      "schedule": "0 2 * * *"
    },
    {
      "path": "/api/cron/health-check",
      "schedule": "0 */6 * * *"
    }
  ]
}
```

### 2. GitHub Actions（バックアップシステム）

**ワークフローファイル:**
```yaml
# .github/workflows/data-backup.yml
name: Tax Data Backup and Verification

on:
  schedule:
    # 毎週日曜日午前3時（JST）に実行
    - cron: '0 18 * * 6'
  workflow_dispatch:
    inputs:
      force_update:
        description: 'Force data update even if no changes'
        required: false
        default: 'false'

jobs:
  backup-and-verify:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout repository
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Fetch and backup tax data
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
        NOTIFICATION_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
      run: |
        python scripts/backup_tax_data.py
        
    - name: Verify primary system health
      run: |
        python scripts/verify_primary_system.py
        
    - name: Commit and push changes
      if: success()
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add data/backups/
        git diff --staged --quiet || git commit -m "Weekly data backup $(date +'%Y-%m-%d')"
        git push
        
    - name: Notify on failure
      if: failure()
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

**バックアップスクリプト:**
```python
# scripts/backup_tax_data.py
import os
import json
import sqlite3
from datetime import datetime
import requests

def backup_current_data():
    """現在のデータベースからデータをバックアップ"""
    db_path = os.getenv('DATABASE_PATH', 'data/stock_valuator.db')
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 会社規模判定基準データを取得
        cursor.execute("SELECT * FROM company_size_criteria")
        criteria_data = [dict(row) for row in cursor.fetchall()]
        
        # 類似業種比準価額データを取得
        cursor.execute("SELECT * FROM similar_industry_data")
        industry_data = [dict(row) for row in cursor.fetchall()]
    
    # バックアップファイルに保存
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'criteria_data': criteria_data,
        'industry_data': industry_data
    }
    
    backup_dir = 'data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_file = f"{backup_dir}/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"Backup created: {backup_file}")
    return backup_file

def verify_primary_system():
    """プライマリシステムの動作確認"""
    health_check_url = os.getenv('VERCEL_HEALTH_CHECK_URL')
    
    if not health_check_url:
        print("Health check URL not configured")
        return False
    
    try:
        response = requests.get(health_check_url, timeout=30)
        if response.status_code == 200:
            print("Primary system is healthy")
            return True
        else:
            print(f"Primary system unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"Primary system check failed: {e}")
        return False

if __name__ == "__main__":
    backup_file = backup_current_data()
    system_healthy = verify_primary_system()
    
    if not system_healthy:
        print("WARNING: Primary system appears to be unhealthy")
        # Slack通知などの処理
```

### 3. Flask管理画面（緊急対応用）

**管理画面のルート:**
```python
# backend/admin_routes.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from werkzeug.security import check_password_hash
import json
import sqlite3
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # 簡単な認証（本番では適切な認証システムを使用）
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

def get_system_status():
    """システムの現在状態を取得"""
    return {
        'last_update': get_last_update_time(),
        'total_records': get_total_record_count(),
        'system_health': check_system_health(),
        'next_scheduled_update': get_next_scheduled_time()
    }

def update_database_manual(data):
    """手動でのデータベース更新"""
    with sqlite3.connect('data/stock_valuator.db') as conn:
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
```

## 実装手順

### Phase 1: Vercel環境の準備（1週間）

1. **環境変数の設定**
   ```bash
   # Vercel CLI
   vercel env add DATABASE_URL
   vercel env add SLACK_WEBHOOK_URL
   vercel env add ADMIN_PASSWORD_HASH
   ```

2. **データベース移行**
   - Vercel PostgresまたはPlanetScaleの設定
   - 既存SQLiteデータの移行スクリプト作成・実行

3. **基本的なCron Job実装**
   - データ取得ロジックの実装
   - 基本的なエラーハンドリング

### Phase 2: GitHub Actions統合（1週間）

1. **リポジトリシークレットの設定**
   ```
   DATABASE_URL
   SLACK_WEBHOOK
   VERCEL_HEALTH_CHECK_URL
   ```

2. **バックアップワークフローの実装**
   - 週次バックアップスクリプト
   - プライマリシステム監視機能

### Phase 3: 管理画面の実装（1週間）

1. **認証システムの実装**
   - セッション管理
   - パスワードハッシュ化

2. **管理機能の実装**
   - 手動更新機能
   - システム状態表示
   - ログ閲覧機能

### Phase 4: テストと最適化（1週間）

1. **統合テスト**
   - 各システム間の連携確認
   - エラーケースのテスト

2. **パフォーマンス最適化**
   - データベースクエリの最適化
   - キャッシュ機能の実装

## 運用開始後の監視項目

- Vercel関数の実行ログ
- GitHub Actionsの実行状況
- データベースの整合性
- エラー通知の受信状況
- システムレスポンス時間

この実装により、堅牢で保守しやすいデータ更新システムが構築できます。


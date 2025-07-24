# スマート更新戦略

## 概要

国税庁サーバーへの負荷を最小化し、確実なデータ更新を実現するためのインテリジェントな更新戦略について説明します。

## 🎯 **推奨アプローチ: ハイブリッド方式**

### **1. 軽量監視 + 手動承認**

#### **監視方式**
- **頻度**: 週1回（168時間間隔）
- **方法**: HEADリクエストによる軽量チェック
- **対象**: Last-Modified、ETagヘッダーの変更検出

#### **承認フロー**
```
1. 軽量チェック → 更新検出
2. 管理者通知 → メール/Slack
3. 手動承認 → 管理画面/CLI
4. 更新実行 → 確実なデータ取得
```

### **2. 段階的チェック戦略**

#### **Phase 1: 軽量チェック**
```python
# HEADリクエスト（10秒タイムアウト）
response = session.head(url, timeout=10)
last_modified = response.headers.get('Last-Modified')
etag = response.headers.get('ETag')
```

#### **Phase 2: 詳細チェック**
```python
# 更新がある場合のみ詳細チェック
if update_detected:
    full_content = session.get(url, timeout=30)
    content_hash = hashlib.md5(full_content.content).hexdigest()
```

#### **Phase 3: 管理者承認**
```python
# 更新承認後の実行
if admin_approved:
    execute_update(data_type)
```

## 🛠 **実装システム**

### **1. スマート更新システム**

#### **主要機能**
- **軽量監視**: HEADリクエストによる効率的なチェック
- **変更検出**: Last-Modified、ETag、コンテンツハッシュの比較
- **通知システム**: メール、Slack、Webhook通知
- **承認管理**: 管理者による手動承認フロー
- **履歴管理**: 更新履歴の完全な記録

#### **設定例**
```python
config = {
    'check_interval_hours': 168,  # 週1回
    'lightweight_check': True,
    'notification_enabled': True,
    'auto_update': False,  # 手動承認のみ
    'timeout': 10,  # 軽量チェック用
    'notification_email': 'admin@example.com'
}
```

### **2. 使用方法**

#### **軽量チェック**
```bash
# 週1回の軽量チェック
python tools/smart_updater_runner.py --mode check

# カスタム間隔でのチェック
python tools/smart_updater_runner.py --mode check --interval 72
```

#### **更新承認**
```bash
# 特定データタイプの更新承認
python tools/smart_updater_runner.py --mode approve \
    --data-type comparable --admin-user admin

# 全データタイプの更新承認
python tools/smart_updater_runner.py --mode approve \
    --data-type all --admin-user admin
```

#### **状況確認**
```bash
# 更新状況の確認
python tools/smart_updater_runner.py --mode status

# 更新履歴の確認
python tools/smart_updater_runner.py --mode history
```

## 📊 **負荷軽減効果**

### **1. ネットワーク負荷の削減**

#### **従来方式**
- **リクエスト頻度**: 24時間ごと
- **リクエストサイズ**: フルコンテンツ取得
- **年間リクエスト数**: 365回
- **データ転送量**: 約365MB/年

#### **スマート方式**
- **リクエスト頻度**: 週1回
- **リクエストサイズ**: ヘッダーのみ
- **年間リクエスト数**: 52回
- **データ転送量**: 約5MB/年

### **2. サーバー負荷の削減**

#### **負荷削減率**
- **リクエスト数**: 85%削減
- **データ転送量**: 98%削減
- **処理時間**: 90%削減

### **3. 信頼性の向上**

#### **エラー耐性**
- **ネットワーク障害**: 軽量チェックによる影響最小化
- **タイムアウト**: 短縮されたタイムアウト設定
- **再試行**: 指数バックオフによる適応的再試行

## 🔄 **運用フロー**

### **1. 定期監視**

#### **cron設定例**
```bash
# 毎週月曜日の午前9時に軽量チェック
0 9 * * 1 cd /path/to/stock-valuation/backend && \
python tools/smart_updater_runner.py --mode check
```

#### **systemd設定例**
```ini
[Unit]
Description=Smart Tax Data Updater
After=network.target

[Service]
Type=oneshot
User=www-data
WorkingDirectory=/path/to/stock-valuation/backend
ExecStart=/usr/bin/python3 tools/smart_updater_runner.py --mode check
```

### **2. 通知管理**

#### **メール通知設定**
```python
notification_config = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'username': 'noreply@stock-valuator-pro.com',
    'password': 'app_password',
    'recipients': ['admin@stock-valuator-pro.com']
}
```

#### **Slack通知設定**
```python
slack_config = {
    'webhook_url': 'https://hooks.slack.com/services/...',
    'channel': '#tax-data-updates',
    'username': 'Stock Valuator Pro'
}
```

### **3. 管理画面統合**

#### **Web UI機能**
- **更新状況ダッシュボード**: リアルタイム状況表示
- **承認インターフェース**: ワンクリック承認
- **履歴表示**: 更新履歴の詳細表示
- **設定管理**: 通知設定の変更

## 🛡 **セキュリティ対策**

### **1. アクセス制御**

#### **User-Agent設定**
```python
headers = {
    'User-Agent': 'StockValuatorPro/1.0 (https://stock-valuator-pro.com)'
}
```

#### **レート制限対応**
```python
# 適切な間隔でのアクセス
time.sleep(random.uniform(1, 3))  # ランダムな遅延
```

### **2. データ保護**

#### **暗号化通信**
- **HTTPS**: 全通信の暗号化
- **証明書検証**: 適切な証明書検証

#### **データ整合性**
```python
# コンテンツハッシュによる整合性チェック
content_hash = hashlib.md5(content).hexdigest()
if content_hash != expected_hash:
    raise ValueError("データ整合性エラー")
```

## 📈 **監視とメトリクス**

### **1. 監視項目**

#### **パフォーマンス指標**
- **チェック成功率**: 目標99%以上
- **平均レスポンス時間**: 目標5秒以下
- **エラー率**: 目標1%以下

#### **運用指標**
- **更新頻度**: 月間更新回数
- **承認率**: 更新検出時の承認率
- **通知到達率**: 通知の成功率

### **2. ログ管理**

#### **ログレベル**
- **INFO**: 通常の操作ログ
- **WARNING**: 警告メッセージ
- **ERROR**: エラーメッセージ
- **DEBUG**: デバッグ情報

#### **ログ分析**
```bash
# エラー率の確認
grep ERROR smart_updater.log | wc -l

# 更新頻度の確認
grep "更新が検出されました" smart_updater.log | wc -l

# 承認率の確認
grep "承認" smart_updater.log | wc -l
```

## 🚀 **今後の拡張計画**

### **1. 短期計画（3ヶ月以内）**
- **Web UI**: 管理画面の実装
- **通知強化**: 複数チャンネル対応
- **自動化**: 特定条件での自動承認

### **2. 中期計画（6ヶ月以内）**
- **機械学習**: 更新パターンの学習
- **予測機能**: 更新タイミングの予測
- **API提供**: 外部システムとの連携

### **3. 長期計画（1年以内）**
- **AI活用**: インテリジェントな更新判断
- **クラウド対応**: クラウド環境での運用
- **国際展開**: 他国の税務データ対応

## ✅ **推奨設定**

### **本番環境推奨設定**
```python
production_config = {
    'check_interval_hours': 168,  # 週1回
    'lightweight_check': True,
    'notification_enabled': True,
    'auto_update': False,
    'timeout': 10,
    'max_retries': 3,
    'notification_email': 'admin@stock-valuator-pro.com',
    'notification_slack_webhook': 'https://hooks.slack.com/...'
}
```

### **開発環境推奨設定**
```python
development_config = {
    'check_interval_hours': 24,  # 日1回（テスト用）
    'lightweight_check': True,
    'notification_enabled': False,
    'auto_update': True,  # 開発時は自動更新
    'timeout': 5,
    'max_retries': 1
}
```

---

**この戦略により、国税庁サーバーへの負荷を85%削減しながら、確実なデータ更新を実現できます。**

**最終更新日**: 2025年  
**責任者**: システムアーキテクト  
**承認者**: プロジェクトマネージャー 
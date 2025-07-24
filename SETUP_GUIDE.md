# Vercel Postgres セットアップガイド

## 概要

このガイドでは、Stock Valuator ProアプリケーションでVercel Postgresをゼロから設定する手順を説明します。

## 前提条件

- **Vercel CLI** がインストールされている
- **Node.js 18+** がインストールされている
- **GitHubリポジトリ** にプロジェクトがプッシュされている

## セットアップ手順

### 1. Vercelプロジェクトの初期化

```bash
# Vercel CLIでログイン
vercel login

# プロジェクトをVercelにリンク
vercel link

# プロジェクトの設定を確認
vercel env ls
```

### 2. Vercel Postgresの作成

```bash
# Vercel Postgresを作成
vercel storage create postgres

# 作成時に以下の情報を入力：
# - データベース名: stock-valuator-pro
# - リージョン: Tokyo (NRT) [推奨]
# - プラン: Hobby (無料) [開発用]
```

### 3. 環境変数の設定

```bash
# データベースURLを環境変数に追加
vercel env add DATABASE_URL

# 通知用の環境変数を追加
vercel env add SLACK_WEBHOOK_URL
vercel env add EMAIL_SMTP_URL
vercel env add WEBHOOK_URL

# 管理者パスワードハッシュを追加
vercel env add ADMIN_PASSWORD_HASH
```

### 4. 環境変数ファイルの取得

```bash
# ローカル開発用に環境変数を取得
vercel env pull .env.local
```

### 5. 依存関係のインストール

```bash
# Node.js依存関係のインストール
npm install

# Python依存関係のインストール
cd backend
pip install -r requirements.txt
cd ..
```

### 6. データベーススキーマの作成

```bash
# データベーススキーマを作成（サンプルデータなし）
npm run setup:postgres

# または、サンプルデータ付きで作成
npm run setup:postgres:sample
```

### 7. アプリケーションのデプロイ

```bash
# 本番環境にデプロイ
vercel --prod

# または
npm run vercel:deploy
```

## データベーススキーマ

### 作成されるテーブル

1. **comparable_industry_data** - 類似業種比準価額データ
2. **dividend_reduction_rates** - 配当還元率データ
3. **company_size_criteria** - 会社規模判定基準
4. **update_history** - 更新履歴
5. **system_settings** - システム設定

### インデックス

各テーブルには以下のインデックスが作成されます：

- **業種コード** による検索最適化
- **年月** による検索最適化
- **複合キー** による一意性制約

## 設定の確認

### 1. データベース接続の確認

```bash
# ヘルスチェックエンドポイントにアクセス
curl https://your-app.vercel.app/api/health
```

期待される応答：
```json
{
  "status": "healthy",
  "timestamp": "2025-01-XX...",
  "version": "1.0.0",
  "database": {
    "status": "healthy",
    "checks": {
      "connection": "ok",
      "table_comparable_industry_data": "ok",
      "table_dividend_reduction_rates": "ok",
      "table_company_size_criteria": "ok",
      "table_update_history": "ok",
      "table_system_settings": "ok"
    }
  }
}
```

### 2. 統計情報の確認

```bash
# データベース統計情報を取得
curl https://your-app.vercel.app/api/stats
```

### 3. データ取得の確認

```bash
# 類似業種データを取得
curl https://your-app.vercel.app/api/tax-data/comparable

# 配当還元率データを取得
curl https://your-app.vercel.app/api/tax-data/dividend

# 会社規模判定基準を取得
curl https://your-app.vercel.app/api/tax-data/company-size
```

## 開発環境での使用

### 1. ローカル開発サーバーの起動

```bash
# バックエンドサーバーの起動
cd backend
python app.py

# フロントエンドサーバーの起動（別ターミナル）
cd frontend
npm run dev
```

### 2. 環境変数の設定

`.env.local`ファイルが正しく設定されていることを確認：

```env
DATABASE_URL=postgresql://...
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
EMAIL_SMTP_URL=smtp://...
WEBHOOK_URL=https://...
ADMIN_PASSWORD_HASH=...
```

## トラブルシューティング

### よくある問題

#### 1. データベース接続エラー

```bash
# 接続文字列の確認
echo $DATABASE_URL

# 手動で接続テスト
psql $DATABASE_URL -c "SELECT 1;"
```

#### 2. テーブルが存在しない

```bash
# スキーマの再作成
npm run setup:postgres
```

#### 3. 環境変数が設定されていない

```bash
# 環境変数の確認
vercel env ls

# 環境変数の再設定
vercel env pull .env.local
```

#### 4. Vercel Functionsのタイムアウト

`vercel.json`でタイムアウト設定を確認：

```json
{
  "functions": {
    "api/cron/update-tax-data.js": {
      "maxDuration": 300
    }
  }
}
```

## 本番環境での運用

### 1. 監視の設定

- **Vercel Analytics** の有効化
- **ログ監視** の設定
- **アラート** の設定

### 2. バックアップの設定

- **GitHub Actions** による週次バックアップ
- **Vercel Postgres** の自動バックアップ

### 3. セキュリティの設定

- **環境変数** の暗号化
- **アクセス制御** の設定
- **SSL証明書** の確認

## 次のステップ

1. **データの初期投入**: 国税庁データの手動投入
2. **自動更新の設定**: Vercel Cron Jobsの有効化
3. **通知の設定**: Slack・メール通知の設定
4. **監視の設定**: システム監視の有効化

## サポート

問題が発生した場合は、以下を確認してください：

1. **Vercel Dashboard** のログ
2. **GitHub Actions** の実行ログ
3. **データベース接続** の状態
4. **環境変数** の設定

---

**最終更新日**: 2025年  
**バージョン**: 1.0.0 
# Stock Valuator Pro

非上場株式の相続税評価額を自動計算するWebアプリケーション

## 📋 概要

Stock Valuator Proは、複雑な非上場株式の相続税評価額計算を、ガイド付きのインターフェースを通じて誰でも正確に、かつ効率的に行えるようにするWebアプリケーションです。

## 🚀 主要機能

- **評価方式自動判定**: ユーザー入力に基づき、最適な評価方式を自動で判定
- **会社規模判定**: 決算情報と業種から、大・中・小の会社規模を自動判定
- **各評価方式の計算**: 類似業種比準価額、純資産価額、配当還元価額等を計算
- **有利選択提示**: 納税者が選択可能な評価方法がある場合、両方の結果を併記
- **国税庁データ自動更新**: 最新の税務データを自動で取得・更新

## 🛠 技術スタック

### フロントエンド
- **Vue.js 3** (Composition API)
- **Vite** (ビルドツール)
- **TypeScript** (型安全性)
- **Pinia** (状態管理)
- **Vue Router** (ルーティング)
- **Axios** (HTTP通信)
- **Vitest** (テストフレームワーク)
- **ESLint + Prettier** (コード品質)

### バックエンド
- **Python 3.11+**
- **Flask** (Webフレームワーク)
- **Vercel Functions** (サーバーレス)
- **Vercel Postgres** (データベース)
- **pandas** (データ処理)
- **pytest** (テストフレームワーク)
- **requests** (HTTP通信)
- **BeautifulSoup4** (Webスクレイピング)
- **PyPDF2** (PDF解析)

### データ更新システム
- **Vercel Cron Jobs**: 週1回の自動データ更新
- **GitHub Actions**: 週次バックアップとシステム監視
- **軽量監視**: HEADリクエストによる効率的な更新チェック
- **通知機能**: Slack・メール・Webhook通知

## 📦 セットアップ

### 前提条件

- **Node.js 18+** と **npm**
- **Python 3.11+** と **pip**
- **Vercel CLI** がインストールされている

### クイックスタート

```bash
# 1. リポジトリのクローン
git clone https://github.com/your-org/stock-valuation.git
cd stock-valuation

# 2. Vercelプロジェクトの初期化
vercel login
vercel link

# 3. Vercel Postgresの作成
vercel storage create postgres

# 4. 環境変数の設定
vercel env add DATABASE_URL
vercel env add SLACK_WEBHOOK_URL
vercel env add EMAIL_SMTP_URL
vercel env add WEBHOOK_URL
vercel env add ADMIN_PASSWORD_HASH

# 5. 環境変数ファイルの取得
vercel env pull .env.local

# 6. 依存関係のインストール
npm install
cd backend && pip install -r requirements.txt && cd ..

# 7. データベーススキーマの作成
npm run setup:postgres:sample

# 8. アプリケーションのデプロイ
vercel --prod
```

### 詳細セットアップ

詳細なセットアップ手順については、[SETUP_GUIDE.md](SETUP_GUIDE.md)を参照してください。

### フロントエンド

```bash
# フロントエンドディレクトリに移動
cd frontend

# 依存関係のインストール
npm install

# 環境変数ファイルの作成
cp env.example .env

# 開発サーバーの起動
npm run dev
```

### バックエンド

```bash
# バックエンドディレクトリに移動
cd backend

# 仮想環境の作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt

# 開発サーバーの起動
python app.py
```

## 🧪 テスト

### フロントエンドテスト
```bash
cd frontend

# 単体テスト
npm run test

# カバレッジテスト
npm run test:coverage

# UIテスト
npm run test:ui
```

### バックエンドテスト
```bash
cd backend

# 全テスト実行
python run_tests.py

# 特定テスト実行
python run_tests.py --test test_valuation_logic

# カバレッジテスト
python run_tests.py --coverage
```

## 🚀 デプロイ

### フロントエンド（Vercel）

```bash
cd frontend

# 本番ビルド
npm run build

# Vercelにデプロイ
vercel --prod
```

### バックエンド（Vercel Functions）

```bash
# Vercel環境変数の設定
vercel env add DATABASE_URL
vercel env add SLACK_WEBHOOK_URL
vercel env add EMAIL_SMTP_URL
vercel env add WEBHOOK_URL

# デプロイ
vercel --prod
```

### データベース（Vercel Postgres）

```bash
# Vercel Postgresの作成
vercel storage create postgres

# データベースの初期化
vercel env pull .env.local
```

### データ更新システムの設定

```bash
# Vercel Cron Jobs設定
# vercel.jsonで週1回（毎週月曜日午前2時）の自動更新を設定

# GitHub Actions設定
# .github/workflows/data-backup.ymlで週次バックアップを設定

# GitHub Secrets設定
# DATABASE_URL, SLACK_WEBHOOK, VERCEL_HEALTH_CHECK_URL
```

## 📊 監視とログ

### ログファイル
- **フロントエンド**: `frontend/logs/`
- **バックエンド**: `backend/logs/`
- **Vercel Functions**: Vercel Dashboard
- **GitHub Actions**: GitHub Actions ログ

### 監視項目
- **アプリケーション性能**: レスポンス時間、エラー率
- **データ更新状況**: 更新頻度、成功率
- **システムリソース**: CPU、メモリ、ディスク使用量
- **Vercel Functions**: 実行時間、メモリ使用量
- **GitHub Actions**: 実行状況、成功率

## 🔧 開発

### 開発環境のセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/your-org/stock-valuation.git
cd stock-valuation

# フロントエンドセットアップ
cd frontend
npm install
npm run dev

# バックエンドセットアップ
cd ../backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### コード品質チェック

```bash
# フロントエンド
cd frontend
npm run lint
npm run type-check
npm run test

# バックエンド
cd ../backend
python run_tests.py --coverage
```

## 📈 今後の拡張計画

### 短期計画（3ヶ月以内）
- **Webhook通知**: 更新時の自動通知機能
- **メール通知**: エラー発生時のメール通知
- **Web UI**: 管理画面の提供

### 中期計画（6ヶ月以内）
- **機械学習**: PDF解析精度の向上
- **API提供**: 外部システムとの連携
- **監視ダッシュボード**: リアルタイム監視画面

### 長期計画（1年以内）
- **AI活用**: 自動データ検証機能
- **クラウド対応**: クラウド環境での運用
- **国際展開**: 他国の税務データ対応

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

プロジェクトへの貢献を歓迎します。詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

## 📞 サポート

技術的なサポートが必要な場合は、[Issues](https://github.com/your-org/stock-valuation/issues)でお知らせください。

---

**最終更新日**: 2025年  
**バージョン**: 1.0.0  
**責任者**: プロジェクトマネージャー

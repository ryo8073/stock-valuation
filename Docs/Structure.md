.
├── backend/
│   ├── modules/
│   │   └── valuation_logic.py  # 評価額計算ロジック【最重要】
│   ├── app.py                  # バックエンドAPIサーバー
│   └── requirements.txt        # 依存ライブラリ
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── assets/
│   │   │   └── main.css        # スタイルシート
│   │   ├── components/
│   │   │   ├── DisclaimerModal.vue # 免責事項同意モーダル
│   │   │   ├── EvaluationForm.vue  # 評価入力フォーム
│   │   │   └── ResultDisplay.vue   # 結果表示画面
│   │   ├── services/
│   │   │   └── api.js          # API通信サービス
│   │   ├── App.vue             # ルートコンポーネント
│   │   └── main.js             # アプリケーションのエントリポイント
│   ├── package.json          # プロジェクト設定
│   └── vite.config.js        # Vite設定ファイル
└── README.md                     # プロジェクト概要・セットアップ手順

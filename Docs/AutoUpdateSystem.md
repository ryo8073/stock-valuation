# 国税庁データ自動更新システム

## 概要

Stock Valuator Proの国税庁データ自動更新システムについて説明します。このシステムは、国税庁ウェブサイトを定期的に監視し、新しいデータを自動で取得・更新する機能を提供します。

## 1. システム概要

### 1.1 目的
- **自動化**: 手動でのデータ取得・更新作業の自動化
- **正確性**: 最新の国税庁データの確実な反映
- **効率性**: 運用コストの削減とデータ品質の向上
- **信頼性**: データの整合性とバックアップの確保

### 1.2 対象データ
- **類似業種比準価額データ**: 業種別の平均株価・配当・利益・純資産
- **配当還元率データ**: 資本金規模別の配当還元率
- **会社規模判定基準データ**: 業種・規模別の判定基準

## 2. システム構成

### 2.1 主要コンポーネント

```
自動更新システム
├── TaxDataAutoUpdater      # メイン更新クラス
├── TaxDataManager          # データ管理クラス
├── スケジューラー           # 定期実行機能
├── PDF解析器               # PDF→CSV変換
├── データ検証器             # 整合性チェック
└── バックアップシステム     # データ保護
```

### 2.2 ファイル構成
```
backend/
├── modules/
│   ├── tax_data_auto_updater.py    # 自動更新システム
│   └── tax_data_manager.py         # データ管理
├── tools/
│   └── auto_updater_runner.py      # 実行スクリプト
├── tests/
│   └── test_auto_updater.py        # テスト
└── downloads/                      # ダウンロードファイル
    └── backups/                    # バックアップ
```

## 3. 機能詳細

### 3.1 自動監視機能

#### 3.1.1 更新チェック
```python
# 更新の有無をチェック
def check_for_updates(self) -> bool:
    """更新の有無をチェック"""
    updates_available = {
        'comparable': self._check_comparable_data_updates(),
        'dividend': self._check_dividend_data_updates(),
        'company_size': self._check_company_size_data_updates()
    }
    return any(updates_available.values())
```

#### 3.1.2 監視対象URL
- **類似業種比準価額**: `https://www.nta.go.jp/taxanswer/sozoku/4608.htm`
- **配当還元率**: `https://www.nta.go.jp/taxanswer/sozoku/4609.htm`
- **会社規模判定基準**: `https://www.nta.go.jp/taxanswer/sozoku/4610.htm`

### 3.2 データ取得機能

#### 3.2.1 PDFダウンロード
```python
def _download_file(self, url: str, file_path: Path) -> bool:
    """ファイルのダウンロード"""
    response = self.session.get(url, timeout=self.config['timeout'])
    response.raise_for_status()
    
    with open(file_path, 'wb') as f:
        f.write(response.content)
    return True
```

#### 3.2.2 PDF解析
```python
def _convert_pdf_to_csv(self, pdf_path: Path, data_type: str) -> Optional[Path]:
    """PDFからCSVへの変換"""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    # データタイプに応じた解析
    df = self._parse_data_by_type(text, data_type)
    csv_path = pdf_path.with_suffix('.csv')
    df.to_csv(csv_path, index=False, encoding='utf-8')
    return csv_path
```

### 3.3 データ処理機能

#### 3.3.1 類似業種データの解析
```python
def _parse_comparable_data(self, text: str) -> pd.DataFrame:
    """類似業種データの解析"""
    data = []
    lines = text.split('\n')
    
    for line in lines:
        if re.match(r'\d+', line.strip()):
            parts = line.split()
            if len(parts) >= 5:
                data.append({
                    'industry_code': parts[0],
                    'industry_name': parts[1],
                    'average_price': float(parts[2]),
                    'average_dividend': float(parts[3]),
                    'average_profit': float(parts[4]),
                    'average_net_assets': float(parts[5]) if len(parts) > 5 else 0
                })
    
    return pd.DataFrame(data)
```

#### 3.3.2 配当還元率データの解析
```python
def _parse_dividend_data(self, text: str) -> pd.DataFrame:
    """配当還元率データの解析"""
    data = []
    lines = text.split('\n')
    
    for line in lines:
        if re.match(r'\d+', line.strip()):
            parts = line.split()
            if len(parts) >= 3:
                data.append({
                    'capital_range_min': int(parts[0]),
                    'capital_range_max': int(parts[1]),
                    'reduction_rate': float(parts[2])
                })
    
    return pd.DataFrame(data)
```

### 3.4 スケジューリング機能

#### 3.4.1 定期実行
```python
def start_scheduler(self):
    """スケジューラーを開始"""
    # 毎日指定時間にチェック
    schedule.every(self.config['check_interval_hours']).hours.do(self._scheduled_check)
    
    # 初回チェックを即座に実行
    self._scheduled_check()
    
    # スケジューラーを実行
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1分ごとにチェック
```

#### 3.4.2 実行モード
- **デーモンモード**: 継続的に監視・更新
- **手動モード**: 1回限りの更新実行
- **チェックモード**: 更新の有無のみ確認

## 4. 使用方法

### 4.1 基本的な使用方法

#### 4.1.1 デーモンモード（推奨）
```bash
# 24時間ごとに自動チェック・更新
python backend/tools/auto_updater_runner.py --mode daemon --check-interval 24
```

#### 4.1.2 手動更新
```bash
# 1回限りの手動更新
python backend/tools/auto_updater_runner.py --mode manual
```

#### 4.1.3 更新チェック
```bash
# 更新の有無のみ確認
python backend/tools/auto_updater_runner.py --mode check
```

### 4.2 設定のカスタマイズ

#### 4.2.1 チェック間隔の変更
```bash
# 12時間ごとにチェック
python backend/tools/auto_updater_runner.py --mode daemon --check-interval 12
```

#### 4.2.2 データベースパスの指定
```bash
# カスタムデータベースパス
python backend/tools/auto_updater_runner.py --mode manual --db-path /path/to/custom.db
```

### 4.3 システムサービスとしての実行

#### 4.3.1 systemdサービスファイル
```ini
[Unit]
Description=Tax Data Auto Updater
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/stock-valuation/backend
ExecStart=/usr/bin/python3 tools/auto_updater_runner.py --mode daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4.3.2 サービスの有効化
```bash
# サービスファイルを配置
sudo cp tax-data-updater.service /etc/systemd/system/

# サービスを有効化・開始
sudo systemctl enable tax-data-updater
sudo systemctl start tax-data-updater

# ステータス確認
sudo systemctl status tax-data-updater
```

## 5. エラーハンドリング

### 5.1 ネットワークエラー
- **再試行機能**: 最大3回の自動再試行
- **指数バックオフ**: 再試行間隔の自動調整
- **タイムアウト設定**: 30秒のタイムアウト

### 5.2 データ解析エラー
- **フォールバック**: デフォルトデータの使用
- **ログ記録**: 詳細なエラーログ
- **部分更新**: 成功したデータのみ更新

### 5.3 データベースエラー
- **トランザクション管理**: 整合性の確保
- **ロールバック機能**: エラー時の復旧
- **バックアップ**: 更新前の自動バックアップ

## 6. 監視とログ

### 6.1 ログファイル
- **`auto_updater.log`**: 自動更新システムのログ
- **`tax_data_updater.log`**: データ更新の詳細ログ
- **`data_import.log`**: データインポートのログ

### 6.2 ログレベル
- **INFO**: 通常の操作ログ
- **WARNING**: 警告メッセージ
- **ERROR**: エラーメッセージ
- **DEBUG**: デバッグ情報

### 6.3 監視項目
- **更新頻度**: データの更新状況
- **成功率**: 更新処理の成功率
- **処理時間**: 更新処理にかかる時間
- **エラー率**: エラーの発生頻度

## 7. セキュリティ

### 7.1 アクセス制御
- **User-Agent設定**: 適切なブラウザ識別
- **レート制限**: 過度なアクセスの防止
- **タイムアウト**: 長時間接続の防止

### 7.2 データ保護
- **暗号化通信**: HTTPS接続の使用
- **データ検証**: ダウンロードデータの整合性チェック
- **バックアップ**: 更新前の自動バックアップ

## 8. パフォーマンス

### 8.1 最適化
- **セッション再利用**: HTTP接続の効率化
- **並列処理**: 複数データの同時処理
- **メモリ管理**: 大容量データの効率的処理

### 8.2 リソース使用量
- **CPU使用率**: 通常時5%以下
- **メモリ使用量**: 100MB以下
- **ディスク使用量**: 月間1GB以下

## 9. トラブルシューティング

### 9.1 よくある問題

#### 9.1.1 ネットワーク接続エラー
```bash
# ネットワーク接続を確認
ping www.nta.go.jp

# DNS解決を確認
nslookup www.nta.go.jp

# プロキシ設定を確認
echo $http_proxy
echo $https_proxy
```

#### 9.1.2 PDF解析エラー
```bash
# PDFライブラリの確認
python -c "import PyPDF2; print(PyPDF2.__version__)"

# サンプルPDFでのテスト
python -c "from modules.tax_data_auto_updater import TaxDataAutoUpdater; updater = TaxDataAutoUpdater(None); print('PDF解析機能正常')"
```

#### 9.1.3 データベースエラー
```bash
# データベースファイルの権限確認
ls -la tax_data.db

# データベースの整合性チェック
sqlite3 tax_data.db "PRAGMA integrity_check;"
```

### 9.2 ログ解析
```bash
# エラーログの確認
grep ERROR auto_updater.log

# 最新の更新状況確認
tail -f auto_updater.log

# 統計情報の確認
grep "更新が検出されました" auto_updater.log | wc -l
```

## 10. 今後の拡張計画

### 10.1 短期計画（3ヶ月以内）
- **Webhook通知**: 更新時の自動通知機能
- **メール通知**: エラー発生時のメール通知
- **Web UI**: 管理画面の提供

### 10.2 中期計画（6ヶ月以内）
- **機械学習**: PDF解析精度の向上
- **API提供**: 外部システムとの連携
- **監視ダッシュボード**: リアルタイム監視画面

### 10.3 長期計画（1年以内）
- **AI活用**: 自動データ検証機能
- **クラウド対応**: クラウド環境での運用
- **国際展開**: 他国の税務データ対応

---

**最終更新日**: 2025年  
**責任者**: 自動更新システム開発チーム  
**承認者**: プロジェクトマネージャー 
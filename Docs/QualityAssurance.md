# 品質保証ドキュメント

## 概要

Stock Valuator Proの品質保証システムについて説明します。このドキュメントでは、テスト戦略、データ管理、品質基準、および継続的な品質改善プロセスについて詳しく説明します。

## 1. 品質保証戦略

### 1.1 品質保証の目的
- **計算精度の保証**: 国税庁基準に準拠した正確な評価計算
- **データ整合性の確保**: 国税庁データの正確な管理と更新
- **システム安定性の維持**: 高可用性とパフォーマンスの確保
- **ユーザビリティの向上**: 直感的で使いやすいインターフェース

### 1.2 品質保証の範囲
- **機能テスト**: 全ての評価方式の計算ロジック
- **統合テスト**: フロントエンド・バックエンド連携
- **データテスト**: 国税庁データの整合性と更新プロセス
- **パフォーマンステスト**: レスポンス時間とスループット
- **セキュリティテスト**: 入力値検証とデータ保護

## 2. テスト戦略

### 2.1 テストピラミッド

```
    E2E Tests (少数)
        /\
       /  \
   Integration Tests
      /\
     /  \
Unit Tests (多数)
```

### 2.2 テストレベル

#### 2.2.1 ユニットテスト
- **対象**: 個別の関数・メソッド
- **実行頻度**: 開発時・コミット時
- **自動化**: 完全自動化

**テスト対象**:
- `valuation_logic.py`の各計算関数
- `tax_data_manager.py`のデータ操作関数
- ユーティリティ関数

#### 2.2.2 統合テスト
- **対象**: モジュール間の連携
- **実行頻度**: プルリクエスト時
- **自動化**: 完全自動化

**テスト対象**:
- APIエンドポイント
- データベース操作
- フロントエンド・バックエンド連携

#### 2.2.3 E2Eテスト
- **対象**: ユーザーシナリオ全体
- **実行頻度**: リリース前
- **自動化**: 部分自動化

**テスト対象**:
- 評価フォーム入力から結果表示まで
- エラーハンドリング
- レスポンシブデザイン

### 2.3 テスト実行

```bash
# 全テスト実行
python backend/run_tests.py

# 特定テスト実行
python backend/run_tests.py --test tests.test_valuation_logic

# カバレッジテスト実行
python backend/run_tests.py --coverage
```

## 3. データ管理品質保証

### 3.1 国税庁データ管理

#### 3.1.1 データ更新プロセス
1. **データ取得**: 国税庁ウェブサイトからの手動ダウンロード
2. **データ変換**: CSV形式への変換
3. **データ検証**: 形式・内容の妥当性チェック
4. **データインポート**: データベースへの格納
5. **データ検証**: インポート後の整合性チェック

#### 3.1.2 データ品質基準
- **完全性**: 必須項目の欠損なし
- **正確性**: 国税庁データとの一致
- **一貫性**: データ形式の統一
- **時効性**: 最新データの反映

#### 3.1.3 データ検証ルール
```python
# データ検証例
def validate_comparable_industry_data(data):
    """類似業種比準価額データの検証"""
    required_fields = ['industry_code', 'average_price', 'average_dividend']
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"必須項目が欠損: {field}")
    
    if data['average_price'] <= 0:
        raise ValueError("平均株価は正の値である必要があります")
    
    if data['average_dividend'] < 0:
        raise ValueError("平均配当は0以上の値である必要があります")
```

### 3.2 データベース設計

#### 3.2.1 テーブル構造
```sql
-- 類似業種比準価額データ
CREATE TABLE comparable_industry_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    industry_code TEXT NOT NULL,
    industry_name TEXT NOT NULL,
    average_price REAL NOT NULL,
    average_dividend REAL NOT NULL,
    average_profit REAL NOT NULL,
    average_net_assets REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, month, industry_code)
);

-- 配当還元率データ
CREATE TABLE dividend_reduction_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    capital_range_min INTEGER NOT NULL,
    capital_range_max INTEGER NOT NULL,
    reduction_rate REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, month, capital_range_min, capital_range_max)
);

-- 会社規模判定基準
CREATE TABLE company_size_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    industry_type TEXT NOT NULL,
    size_category TEXT NOT NULL,
    employee_min INTEGER,
    employee_max INTEGER,
    asset_min INTEGER,
    asset_max INTEGER,
    sales_min INTEGER,
    sales_max INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, month, industry_type, size_category)
);
```

#### 3.2.2 データ整合性制約
- **外部キー制約**: 業種コードの整合性
- **チェック制約**: 数値範囲の妥当性
- **ユニーク制約**: 重複データの防止
- **NOT NULL制約**: 必須項目の確保

## 4. 計算精度保証

### 4.1 計算ロジック検証

#### 4.1.1 テストケース設計
```python
# 純資産価額方式のテストケース
test_cases = [
    {
        "name": "通常ケース",
        "input": {
            "assets": 1000000000,
            "liabilities": 500000000,
            "unrealized_gains": 200000000,
            "shares": 1000
        },
        "expected": 426000  # (1000000000 - 500000000 - 74000000) / 1000
    },
    {
        "name": "含み益なし",
        "input": {
            "assets": 1000000000,
            "liabilities": 500000000,
            "unrealized_gains": 0,
            "shares": 1000
        },
        "expected": 500000  # (1000000000 - 500000000) / 1000
    }
]
```

#### 4.1.2 境界値テスト
- **最小値**: 株式数1株、資産0円
- **最大値**: 大企業の資産・売上
- **ゼロ値**: 配当0円、利益0円
- **負の値**: 負債が資産を上回る場合

### 4.2 計算精度基準
- **整数計算**: 最終結果は整数に丸める
- **小数点以下**: 中間計算は高精度で保持
- **誤差許容**: 国税庁基準との誤差±1円以内

## 5. パフォーマンス保証

### 5.1 パフォーマンス基準
- **レスポンス時間**: 3秒以内
- **スループット**: 100リクエスト/分
- **メモリ使用量**: 512MB以下
- **CPU使用率**: 80%以下

### 5.2 パフォーマンステスト
```python
def test_performance():
    """パフォーマンステスト"""
    start_time = time.time()
    
    # 100回の評価計算を実行
    for i in range(100):
        result = evaluate_stock(sample_data)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 1回あたりの平均時間を計算
    avg_time = execution_time / 100
    
    assert avg_time < 0.03  # 30ms以内
```

## 6. セキュリティ保証

### 6.1 入力値検証
```python
def validate_input_data(data):
    """入力値の検証"""
    # 数値範囲チェック
    if data.get('shares_outstanding', 0) <= 0:
        raise ValueError("発行済株式数は正の値である必要があります")
    
    # 文字列長チェック
    if len(data.get('industry_code', '')) > 10:
        raise ValueError("業種コードが長すぎます")
    
    # SQLインジェクション対策
    if any(char in data.get('industry_code', '') for char in [';', '--', '/*']):
        raise ValueError("無効な文字が含まれています")
```

### 6.2 データ保護
- **暗号化**: 機密データの暗号化保存
- **アクセス制御**: データベースアクセス権限の管理
- **ログ管理**: アクセスログの記録と監視

## 7. 継続的品質改善

### 7.1 品質メトリクス
- **テストカバレッジ**: 90%以上
- **バグ密度**: 1000行あたり1件以下
- **コード複雑度**: 循環複雑度10以下
- **技術的負債**: 5%以下

### 7.2 品質監視
- **自動テスト**: CI/CDパイプラインでの自動実行
- **静的解析**: コード品質の自動チェック
- **パフォーマンス監視**: 本番環境での継続監視
- **ユーザーフィードバック**: 定期的なユーザー調査

### 7.3 品質改善プロセス
1. **問題発見**: テスト・監視・フィードバック
2. **原因分析**: 根本原因の特定
3. **改善策立案**: 具体的な改善策の策定
4. **実装**: 改善策の実装
5. **検証**: 改善効果の確認
6. **標準化**: 成功した改善策の標準化

## 8. 品質保証チェックリスト

### 8.1 リリース前チェックリスト
- [ ] 全テストが成功している
- [ ] テストカバレッジが90%以上
- [ ] パフォーマンス基準を満たしている
- [ ] セキュリティチェックが完了している
- [ ] ドキュメントが更新されている
- [ ] ユーザー受け入れテストが完了している

### 8.2 データ更新チェックリスト
- [ ] 国税庁データの取得が完了している
- [ ] データ形式の検証が完了している
- [ ] データインポートが成功している
- [ ] データ整合性チェックが完了している
- [ ] バックアップが作成されている

## 9. 品質保証ツール

### 9.1 テストツール
- **pytest**: Pythonテストフレームワーク
- **coverage**: テストカバレッジ測定
- **unittest**: 標準テストライブラリ

### 9.2 静的解析ツール
- **flake8**: コードスタイルチェック
- **pylint**: コード品質チェック
- **mypy**: 型チェック

### 9.3 パフォーマンスツール
- **cProfile**: Pythonプロファイラー
- **memory_profiler**: メモリ使用量測定
- **locust**: 負荷テスト

## 10. 品質保証体制

### 10.1 役割と責任
- **開発者**: ユニットテスト・コードレビュー
- **QAエンジニア**: 統合テスト・E2Eテスト
- **プロダクトマネージャー**: ユーザー受け入れテスト
- **DevOpsエンジニア**: パフォーマンス監視・セキュリティ

### 10.2 品質保証プロセス
1. **開発フェーズ**: ユニットテスト・コードレビュー
2. **統合フェーズ**: 統合テスト・静的解析
3. **テストフェーズ**: E2Eテスト・パフォーマンステスト
4. **リリースフェーズ**: 最終検証・デプロイ
5. **運用フェーズ**: 監視・フィードバック収集

---

**最終更新日**: 2024年  
**責任者**: 品質保証チーム  
**承認者**: プロジェクトマネージャー 
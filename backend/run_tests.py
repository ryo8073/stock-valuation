#!/usr/bin/env python3
"""
テスト実行スクリプト
品質保証テストを実行し、結果をレポートする
"""

import unittest
import sys
import os
import time
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_all_tests():
    """全てのテストを実行"""
    print("🧪 Stock Valuator Pro - 品質保証テスト実行")
    print("=" * 50)
    
    # テストディレクトリを検索
    test_dir = Path(__file__).parent / "tests"
    if not test_dir.exists():
        print("❌ テストディレクトリが見つかりません")
        return False
    
    # テストファイルを検索
    test_files = list(test_dir.glob("test_*.py"))
    if not test_files:
        print("❌ テストファイルが見つかりません")
        return False
    
    print(f"📁 テストファイル数: {len(test_files)}")
    for test_file in test_files:
        print(f"  - {test_file.name}")
    
    # テストスイートを作成
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for test_file in test_files:
        # テストファイルをインポート
        module_name = f"tests.{test_file.stem}"
        try:
            module = __import__(module_name, fromlist=[''])
            tests = loader.loadTestsFromModule(module)
            suite.addTests(tests)
        except ImportError as e:
            print(f"⚠️  テストファイルの読み込みに失敗: {test_file.name} - {e}")
    
    if not suite.countTestCases():
        print("❌ 実行可能なテストが見つかりません")
        return False
    
    print(f"📊 実行予定テスト数: {suite.countTestCases()}")
    print()
    
    # テストを実行
    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    end_time = time.time()
    
    # 結果を表示
    print()
    print("=" * 50)
    print("📈 テスト結果サマリー")
    print("=" * 50)
    print(f"実行時間: {end_time - start_time:.2f}秒")
    print(f"実行テスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🚨 エラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    # 成功判定
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n✅ 全てのテストが成功しました！")
    else:
        print(f"\n❌ {len(result.failures) + len(result.errors)}件のテストが失敗しました")
    
    return success

def run_specific_test(test_name):
    """特定のテストを実行"""
    print(f"🧪 特定テスト実行: {test_name}")
    print("=" * 50)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_name)
    
    if not suite.countTestCases():
        print(f"❌ テスト '{test_name}' が見つかりません")
        return False
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\n✅ テスト '{test_name}' が成功しました！")
    else:
        print(f"\n❌ テスト '{test_name}' が失敗しました")
    
    return success

def run_coverage_test():
    """カバレッジテストを実行"""
    try:
        import coverage
        print("📊 カバレッジテスト実行")
        print("=" * 50)
        
        # カバレッジを開始
        cov = coverage.Coverage()
        cov.start()
        
        # テストを実行
        success = run_all_tests()
        
        # カバレッジを停止してレポート
        cov.stop()
        cov.save()
        
        print("\n📈 カバレッジレポート:")
        cov.report()
        
        # HTMLレポートを生成
        cov.html_report(directory='htmlcov')
        print("\n📁 HTMLレポートを生成しました: htmlcov/index.html")
        
        return success
        
    except ImportError:
        print("⚠️  coverageモジュールがインストールされていません")
        print("   インストール方法: pip install coverage")
        return run_all_tests()

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Stock Valuator Pro テスト実行ツール')
    parser.add_argument('--test', help='特定のテストを実行')
    parser.add_argument('--coverage', action='store_true', help='カバレッジテストを実行')
    
    args = parser.parse_args()
    
    if args.test:
        success = run_specific_test(args.test)
    elif args.coverage:
        success = run_coverage_test()
    else:
        success = run_all_tests()
    
    # 終了コードを設定
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 
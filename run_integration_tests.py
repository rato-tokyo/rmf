#!/usr/bin/env python3
"""統合テスト実行スクリプト

使用方法:
    python run_integration_tests.py [--real] [--coverage]

オプション:
    --real      実際のサーバーを使用したテストを実行
    --coverage  カバレッジレポートを生成
"""

import os
import sys
import time
import pytest
import argparse
import coverage
from typing import List

def setup_real_server_check():
    """実サーバーのセットアップ確認"""
    print("注意: RMFサーバー(port:8004)とMCPサーバー(port:8003)が既に起動していることを確認してください")
    print("RMFサーバーが起動していない場合: python rmf_server.py")
    print("MCPサーバーが起動していない場合: python web_mcp.py")
    time.sleep(2)

def run_tests(real_mode: bool = False, enable_coverage: bool = False) -> int:
    """テストを実行する

    Args:
        real_mode (bool): 実サーバーを使用したテストを実行するかどうか
        enable_coverage (bool): カバレッジレポートを生成するかどうか

    Returns:
        int: テスト実行結果のステータスコード
    """
    if real_mode:
        setup_real_server_check()
        test_files = [os.path.join("tests", "real_integration_test.py")]
    else:
        test_files = [os.path.join("tests", "test_rmf_integration.py")]

    pytest_args: List[str] = ["-v", "--asyncio-mode=auto"] + test_files

    if enable_coverage:
        # カバレッジ計測を開始
        cov = coverage.Coverage()
        cov.start()

    # テストを実行
    result = pytest.main(pytest_args)

    if enable_coverage:
        # カバレッジレポートを生成
        cov.stop()
        cov.save()
        
        # レポートを表示
        print("\nカバレッジレポート:")
        cov.report()
        
        # HTMLレポートを生成
        cov.html_report(directory="coverage_report")
        print(f"\nHTMLレポートが生成されました: {os.path.abspath('coverage_report/index.html')}")

    # 結果を表示
    if result == 0:
        print("\n✅ すべてのテストが成功しました！")
    else:
        print(f"\n❌ テストが失敗しました。エラーコード: {result}")

    return result

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="統合テストを実行します")
    parser.add_argument("--real", action="store_true", help="実サーバーを使用したテストを実行")
    parser.add_argument("--coverage", action="store_true", help="カバレッジレポートを生成")
    args = parser.parse_args()

    sys.exit(run_tests(real_mode=args.real, enable_coverage=args.coverage))

if __name__ == "__main__":
    main() 
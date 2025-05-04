# Remote MCP Fetcher Tests (rmf-tests)

Remote MCP Fetcherの統合テストおよびE2Eテストスイートです。

## テストの種類

### 1. 統合テスト (Integration Tests)

複数のコンポーネントを組み合わせたテストを実行します：

- RMFコアとサーバーの連携テスト
- 外部MCPサーバーとの通信テスト
- データベースとの連携テスト
- キャッシュシステムとの連携テスト

### 2. E2Eテスト (End-to-End Tests)

実際のユースケースに基づいた完全なフローのテストを実行します：

- APIエンドポイントの完全なフローテスト
- 実際のMCPサーバーとの通信テスト
- エラーケースの検証
- パフォーマンステスト

## インストール

### 基本インストール

```bash
pip install -e .
```

### 統合テスト用の追加パッケージ

```bash
pip install -e ".[integration]"
```

### E2Eテスト用の追加パッケージ

```bash
pip install -e ".[e2e]"
```

## テストの実行

### 統合テストの実行

```bash
# 全ての統合テストを実行
pytest integration_tests/

# 特定のテストカテゴリーを実行
pytest integration_tests/test_rmf_server/
pytest integration_tests/test_external_mcp/

# 並列実行
pytest -n auto integration_tests/
```

### E2Eテストの実行

```bash
# 全てのE2Eテストを実行
pytest e2e_tests/

# 特定のシナリオを実行
pytest e2e_tests/test_fetch_scenario/
pytest e2e_tests/test_error_handling/

# ブラウザテストの実行
pytest e2e_tests/test_browser/
```

## テスト環境の設定

### 1. Docker環境の準備

統合テストでは、テスト用のMCPサーバーをDockerコンテナとして実行します：

```bash
# テスト用コンテナの起動
docker-compose -f integration_tests/docker-compose.yml up -d

# テストの実行
pytest integration_tests/

# コンテナの停止
docker-compose -f integration_tests/docker-compose.yml down
```

### 2. E2Eテスト環境の準備

```bash
# Playwrightブラウザのインストール
playwright install

# Seleniumドライバーのセットアップ
webdriver-manager update
```

## テストカバレッジ

カバレッジレポートの生成：

```bash
# 統合テストのカバレッジ
pytest --cov=rmf_core --cov=rmf_server integration_tests/

# E2Eテストのカバレッジ
pytest --cov=rmf_core --cov=rmf_server e2e_tests/

# HTMLレポートの生成
coverage html
```

## CI/CD統合

GitHub Actionsワークフローの例：

```yaml
name: Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -e ".[integration]"
      - name: Run integration tests
        run: |
          pytest integration_tests/

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -e ".[e2e]"
      - name: Run E2E tests
        run: |
          pytest e2e_tests/
```

## 注意事項

- 統合テストを実行する前に、必要なDockerコンテナが起動していることを確認してください
- E2Eテストは実際のサーバーに対して実行されるため、テスト環境の準備が必要です
- 機密情報（APIキーなど）はテストコードにハードコードせず、環境変数として管理してください
- 並列テスト実行時は、テスト間の依存関係に注意してください 
# Remote MCP Fetcher プロジェクト

## プロジェクト概要

Remote MCP Fetcher (RMF) は、複数のRemote MCPサーバーを統合し、単一のインターフェースとして提供するリレー型MCPサーバーです。
このプロジェクトは、分散したMCPサービスを効率的に利用するためのソリューションを提供します。

## プロジェクト構成

このプロジェクトは3つの主要なコンポーネントに分かれています：

1. [rmf-core](./rmf-core/README.md): コアライブラリ
   - Remote MCPクライアント実装
   - 設定管理
   - エラーハンドリング
   - ロギング機能

2. [rmf-server](./rmf-server/README.md): サーバーコンポーネント
   - FastAPIベースのWebサーバー
   - 標準MCPエンドポイント
   - ヘルスチェック機能
   - サーバーサイドのロギング

3. [rmf-tests](./rmf-tests/README.md): テストスイート
   - 統合テスト
   - E2Eテスト
   - パフォーマンステスト
   - テスト用のモックサーバー

## システム要件

- Python 3.8以上
- Windows 11 (他の環境での動作は未検証)

## クイックスタート

1. コアライブラリとサーバーのインストール:
```bash
pip install rmf-core rmf-server
```

2. 設定ファイルの作成 (`config.yaml`):
```yaml
remote_mcps:
  - name: "Fetch MCP"
    base_url: "https://fetch-mcp.example.com"
    namespace: "fetch"
    timeout: 30
    retry:
      max_attempts: 3
      initial_delay: 1.0
      max_delay: 5.0
```

3. サーバーの起動:
```bash
rmf-server
```

## 開発者向け情報

### 開発環境のセットアップ

1. リポジトリのクローン:
```bash
git clone https://github.com/yourusername/rmcp.git
cd rmcp
```

2. コアライブラリの開発環境セットアップ:
```bash
cd rmf-core
pip install -e .
cd ..
```

3. サーバーの開発環境セットアップ:
```bash
cd rmf-server
pip install -e ".[dev]"
cd ..
```

4. テスト環境のセットアップ:
```bash
cd rmf-tests
pip install -e ".[integration,e2e]"
cd ..
```

### テスト

各種テストの実行:
```bash
# ユニットテスト
cd rmf-core && pytest tests/
cd ../rmf-server && pytest tests/

# 統合テスト
cd rmf-tests && pytest integration_tests/

# E2Eテスト
cd rmf-tests && pytest e2e_tests/
```

## プロジェクト構造

```
rmcp/
├── rmf-core/              # コアライブラリ
│   ├── rmf/              # RMFコアモジュール
│   ├── tests/            # ユニットテスト
│   ├── setup.py          # パッケージ設定
│   └── README.md         # コアライブラリのドキュメント
│
├── rmf-server/           # サーバーコンポーネント
│   ├── rmf_server/      # サーバー実装
│   ├── tests/           # ユニットテスト
│   ├── setup.py         # パッケージ設定
│   └── README.md        # サーバーのドキュメント
│
├── rmf-tests/           # テストスイート
│   ├── integration_tests/ # 統合テスト
│   ├── e2e_tests/       # E2Eテスト
│   ├── setup.py         # パッケージ設定
│   └── README.md        # テストのドキュメント
│
└── README.md            # プロジェクト全体のドキュメント
```

## 開発ステータス

現在アクティブに開発中のプロジェクトです。新機能の追加やバグ修正を継続的に行っています。

## 注意事項

- 本番環境での使用前に、十分なテストを行ってください
- セキュリティ設定は環境に応じて適切に構成してください
- 大規模な負荷がかかる場合は、適切なスケーリング戦略を検討してください 
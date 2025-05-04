# Remote MCP Fetcher Core (rmf-core)

Remote MCP Fetcherのコアライブラリです。複数のRemote MCPサーバーを統合し、単一のインターフェースとして提供するための基本機能を実装しています。

## 主な機能

- **Remote MCPクライアント**: 各Remote MCPサーバーとの通信を管理
- **設定管理**: YAMLベースの柔軟な設定システム
- **エラーハンドリング**: 包括的なエラー処理とリトライ機能
- **ロギング**: 詳細なログ出力機能

## インストール

```bash
pip install rmf-core
```

## 使用例

```python
from rmf import RemoteMCPFetcher

# RMFインスタンスの作成
rmf = RemoteMCPFetcher("config.yaml")

# ツール一覧の取得
tools = await rmf.get_tools()

# ツールの呼び出し
result = await rmf.call_tool("fetch.get_webpage", {"url": "https://example.com"})
```

## 設定例

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

## 開発

1. リポジトリのクローン:
```bash
git clone https://github.com/yourusername/rmf-core.git
cd rmf-core
```

2. 開発環境のセットアップ:
```bash
pip install -e .
```

## ライセンス

MIT License 
# Remote MCP Fetcher Server (rmf-server)

Remote MCP Fetcherのサーバーコンポーネントです。FastAPIを使用して、標準的なMCPエンドポイントを提供します。

## 主な機能

- **標準MCPエンドポイント**: `/tools/list`と`/tools/call`の提供
- **ヘルスチェック**: サーバーの状態監視
- **エラーハンドリング**: HTTPステータスコードに基づくエラー応答
- **ロギング**: 詳細なサーバーログ

## インストール

```bash
pip install rmf-server
```

## 使用方法

### サーバーの起動

```bash
rmf-server
```

または

```python
from rmf_server.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8004)
```

### エンドポイント

- `GET /tools/list`: 利用可能なツール一覧を取得
- `POST /tools/call`: ツールを呼び出し
- `GET /health`: ヘルスチェック
- `GET /`: サーバー情報

### APIの使用例

```python
import requests

# ツール一覧の取得
response = requests.get("http://localhost:8004/tools/list")
tools = response.json()["tools"]

# ツールの呼び出し
tool_call = {
    "tool": "fetch.get_webpage",
    "arguments": {
        "url": "https://example.com"
    }
}
response = requests.post("http://localhost:8004/tools/call", json=tool_call)
result = response.json()
```

## 開発

1. リポジトリのクローン:
```bash
git clone https://github.com/yourusername/rmf-server.git
cd rmf-server
```

2. 開発環境のセットアップ:
```bash
pip install -e ".[dev]"
```

3. テストの実行:
```bash
pytest tests/
```

## エラーハンドリング

- 404: 要求されたツールが見つからない場合
- 500: サーバー内部エラー
- 503: サーバーが初期化されていない場合
- 504: タイムアウトエラー

## ライセンス

MIT License 
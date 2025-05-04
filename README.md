# Remote MCP Fetcher (RMF)

Remote MCP Fetcher（RMF）は、複数のRemote MCPサーバーを統合し、単一のインターフェースとして提供するリレー型MCPサーバーです。

## 特徴

- 複数のRemote MCPを統合して単一のインターフェースを提供
- 名前空間による各MCPのツール管理
- Server-Sent Events (SSE)によるリアルタイム通知
- 設定ファイルによる柔軟な構成
- 自動リトライ機能
- 詳細なロギング

## 必要条件

- Python 3.8以上
- 必要なパッケージ（requirements.txtに記載）

## インストール

1. リポジトリをクローン：
```bash
git clone [repository-url]
cd rmcp
```

2. 依存パッケージをインストール：
```bash
pip install -r requirements.txt
```

## 設定

`config.yaml`ファイルで設定を行います：

```yaml
remote_mcps:
  - name: "Fetch MCP"
    base_url: "https://fetch-mcp.example.com"
    namespace: "fetch"
    timeout: 30
    retry:
      max_attempts: 3
      initial_delay: 1
      max_delay: 10
    headers:
      User-Agent: "Remote-MCP-Fetcher/1.0"

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "rmf.log"

server:
  sse_enabled: true
  sse_retry_timeout: 3000
  max_concurrent_requests: 10
```

## 使用方法

1. 設定ファイルを準備：
```bash
cp config.yaml.example config.yaml
# config.yamlを編集して設定を行う
```

2. サーバーを起動：
```bash
python rmf-practical.py [config_path]
```

設定ファイルのパスを指定しない場合は、デフォルトで`config.yaml`が使用されます。

## 機能

### 1. ツール一覧の取得

各Remote MCPからツール一覧を取得し、名前空間を付与して統合します。

### 2. ツールの呼び出し

指定されたツールを適切なRemote MCPに転送して実行します。

### 3. SSE通知

以下のイベントをリアルタイムで通知します：

- `tools_updated`: ツール一覧が更新された時
- `tool_called`: ツールが呼び出された時
- `error`: エラーが発生した時

### 4. エラーハンドリング

- 自動リトライ機能
- 詳細なエラーログ
- エラー通知（SSE）

## エラーハンドリング

- ネットワークエラー：自動的にリトライを行います
- 設定エラー：デフォルト設定にフォールバックします
- 実行時エラー：ログに記録し、クライアントに通知します

## ログ

ログは設定ファイルで指定したファイルに出力されます。以下の情報が記録されます：

- サーバーの起動/停止
- ツールの呼び出し
- エラー情報
- 接続/切断情報

## 貢献

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## ライセンス

[ライセンス情報を記載] 
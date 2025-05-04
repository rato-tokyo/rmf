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

## 設定管理

本プロジェクトは環境変数を使用して設定を管理します。

### 環境設定

- `RMF_ENV`: 実行環境
  - `production`: 本番環境（デフォルト）
  - `test`: テスト環境
  - `development`: 開発環境

### MCP設定

- `RMF_MCP_BASE_URL`: MCPのベースURL（デフォルト: `http://localhost:8003`）
- `RMF_MCP_TIMEOUT`: MCPのタイムアウト時間（秒）（デフォルト: `5`）
- `RMF_MCP_RETRY_MAX_ATTEMPTS`: 最大リトライ回数（デフォルト: `3`）
- `RMF_MCP_RETRY_INITIAL_DELAY`: 初期リトライ待機時間（秒）（デフォルト: `0.1`）
- `RMF_MCP_RETRY_MAX_DELAY`: 最大リトライ待機時間（秒）（デフォルト: `1.0`）

### ロギング設定

- `RMF_LOG_LEVEL`: ログレベル（デフォルト: `INFO`）
- `RMF_LOG_FORMAT`: ログフォーマット（デフォルト: `json`）
- `RMF_LOG_FILE`: ログファイル名
  - 本番環境: `rmf.log`
  - テスト環境: `rmf_test.log`
  - 開発環境: `rmf_dev.log`

### サーバー設定

- `RMF_SERVER_SSE_ENABLED`: SSE有効化フラグ（デフォルト: `true`）
- `RMF_SERVER_SSE_RETRY_TIMEOUT`: SSEリトライタイムアウト（ミリ秒）
  - 本番環境: `3000`
  - テスト環境: `1000`
  - 開発環境: `1500`
- `RMF_SERVER_MAX_CONCURRENT_REQUESTS`: 最大同時リクエスト数
  - 本番環境: `10`
  - テスト環境: `5`
  - 開発環境: `3`

### 設定の使用方法

```python
from config import config

# 設定値の取得
mcp_config = config.remote_mcps[0]
log_config = config.logging
server_config = config.server

# 全ての設定を取得
all_config = config.get_config()
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
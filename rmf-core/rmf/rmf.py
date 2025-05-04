"""RMF（Remote MCP Framework）モジュール

リモートMCPとの通信を管理するフレームワーク
"""

import asyncio
import aiohttp
import backoff
from typing import Any, Dict, List, Optional, Union
from .errors import RMFError, ConfigError, TimeoutError, ConnectionError, ToolError
from .logging import get_logger, LogContext, setup_logging

logger = get_logger(__name__)

class RMF:
    """リモートMCPとの通信を管理するクラス"""

    DEFAULT_CONFIG = {
        "logging": {
            "level": "INFO",
            "file": "rmf.log",
            "format": "json"
        },
        "timeouts": {
            "connect": 0.1,
            "read": 5.0
        },
        "retry": {
            "max_attempts": 3,
            "initial_delay": 0.1,
            "max_delay": 1.0
        }
    }

    def __init__(self, config: Dict[str, Any]):
        """初期化
        
        Args:
            config: MCPの設定情報。最低限 "remote_mcps" キーが必要。
              - remote_mcps: リモートMCPの設定リスト
                - name: MCP名
                - base_url: ベースURL
                - timeout: タイムアウト秒数（デフォルト: 5）
                - headers: リクエストヘッダー（オプション）
              - logging: ロギング設定（オプション）
                - level: ログレベル
                - file: ログファイル名
                - format: ログフォーマット
        
        Raises:
            ConfigError: 必須設定が不足している場合
        """
        # 設定の検証
        if not config or not isinstance(config, dict):
            raise ConfigError("設定が提供されていません", {"provided": str(type(config))})
        
        if "remote_mcps" not in config or not config["remote_mcps"]:
            raise ConfigError("remote_mcps 設定が不足しています", {"config_keys": list(config.keys())})
        
        # 設定のマージ（再帰的にデフォルト値を適用）
        self.config = self._merge_config(self.DEFAULT_CONFIG, config)
        
        # リモートMCPの設定を検証・正規化
        self._validate_remote_mcps()
        
        # ロギング設定
        self.logger = setup_logging(self.config["logging"])
        self._session = None
        self._tools_cache = {}
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """設定をマージする（デフォルト値に上書き）
        
        Args:
            default: デフォルト設定
            user: ユーザー設定
            
        Returns:
            マージした設定
        """
        result = default.copy()
        
        for key, value in user.items():
            # 既存のディクショナリ値は再帰的にマージ
            if (
                key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)
            ):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _validate_remote_mcps(self):
        """リモートMCP設定を検証・正規化する
        
        Raises:
            ConfigError: MCP設定が無効な場合
        """
        for i, mcp in enumerate(self.config["remote_mcps"]):
            # 必須パラメータのチェック
            if "name" not in mcp:
                raise ConfigError(
                    f"MCP #{i+1} に name が設定されていません", 
                    {"mcp_index": i}
                )
                
            if "base_url" not in mcp:
                raise ConfigError(
                    f"MCP '{mcp.get('name', f'#{i+1}')}' に base_url が設定されていません",
                    {"mcp_name": mcp.get("name", f"#{i+1}")}
                )
            
            # デフォルト値の設定
            if "timeout" not in mcp:
                mcp["timeout"] = 5.0
                
            if "headers" not in mcp:
                mcp["headers"] = None

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリーポイント"""
        await self.setup()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了処理"""
        await self.cleanup()

    async def setup(self):
        """初期セットアップ"""
        if self._session is None:
            connector = aiohttp.TCPConnector(enable_cleanup_closed=True)
            self._session = aiohttp.ClientSession(connector=connector)

    async def cleanup(self):
        """リソースのクリーンアップ"""
        if self._session is not None:
            await self._session.close()
            self._session = None

    @backoff.on_exception(
        backoff.expo,
        (RMFError, TimeoutError, ConnectionError),
        max_tries=3,
        max_time=30,
    )
    async def _fetch_tools_from_remote(self, mcp_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """リモートMCPからツール一覧を取得

        Args:
            mcp_config: MCPの設定情報

        Returns:
            ツール情報のリスト

        Raises:
            RMFError: ツール一覧の取得に失敗
            TimeoutError: タイムアウト発生
            ConnectionError: 接続エラー発生
        """
        with LogContext(function="_fetch_tools_from_remote", mcp_name=mcp_config["name"]):
            logger.info("ツール一覧の取得開始", details={"base_url": mcp_config["base_url"]})

            try:
                # 接続タイムアウトを短く、読み取りタイムアウトを長めに設定
                timeout = aiohttp.ClientTimeout(
                    total=mcp_config["timeout"],
                    connect=0.1,  # 接続タイムアウトを0.1秒に設定
                    sock_read=5.0  # 読み取りタイムアウトを5秒に設定
                )

                try:
                    async with self._session.get(
                        f"{mcp_config['base_url']}/tools/list",
                        timeout=timeout,
                        headers=mcp_config.get("headers"),
                    ) as response:
                        if response.status == 200:
                            tools = await response.json()
                            logger.info("ツール一覧の取得成功", details={"tool_count": len(tools)})
                            return tools
                        else:
                            raise RMFError(f"ツール一覧の取得エラー: HTTP {response.status}")

                except aiohttp.ClientConnectorError as e:
                    logger.error("ツール一覧の取得エラー", details={"error": str(e)})
                    raise ConnectionError(f"ツール一覧の取得エラー: {str(e)}") from e

                except aiohttp.ClientError as e:
                    logger.error("ツール一覧の取得エラー", details={"error": str(e)})
                    raise ConnectionError(f"ツール一覧の取得エラー: {str(e)}") from e

            except asyncio.TimeoutError as e:
                logger.error("ツール一覧の取得タイムアウト", details={"timeout": mcp_config["timeout"]})
                raise TimeoutError(f"ツール一覧の取得タイムアウト: {mcp_config['timeout']}秒") from e

    @backoff.on_exception(
        backoff.expo,
        (ToolError, TimeoutError, ConnectionError),
        max_tries=3,
        max_time=30,
    )
    async def _call_remote_tool(
        self,
        mcp_config: Dict[str, Any],
        tool: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """リモートツールを呼び出す

        Args:
            mcp_config: MCPの設定情報
            tool: ツール名
            arguments: ツールの引数

        Returns:
            ツールの実行結果

        Raises:
            ToolError: ツール呼び出しに失敗
            TimeoutError: タイムアウト発生
            ConnectionError: 接続エラー発生
        """
        with LogContext(
            function="_call_remote_tool",
            tool=tool,
            arguments=arguments,
            mcp_name=mcp_config["name"],
        ):
            logger.info("ツール呼び出し開始")

            try:
                # 接続タイムアウトを短く、読み取りタイムアウトを長めに設定
                timeout = aiohttp.ClientTimeout(
                    total=mcp_config["timeout"],
                    connect=0.1,  # 接続タイムアウトを0.1秒に設定
                    sock_read=5.0  # 読み取りタイムアウトを5秒に設定
                )

                try:
                    async with self._session.post(
                        f"{mcp_config['base_url']}/tools/call",
                        json={"tool": tool, "arguments": arguments},
                        timeout=timeout,
                        headers=mcp_config.get("headers"),
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info("ツール呼び出し成功", details={"result": result})
                            return result
                        else:
                            raise ToolError(f"ツール呼び出し失敗: {tool} (HTTP {response.status})")

                except aiohttp.ClientConnectorError as e:
                    logger.error("ツール呼び出しエラー", details={"error": str(e)})
                    raise ConnectionError(f"ツール呼び出しエラー: {str(e)}") from e

                except aiohttp.ClientError as e:
                    logger.error("ツール呼び出しエラー", details={"error": str(e)})
                    raise ConnectionError(f"ツール呼び出しエラー: {str(e)}") from e

            except asyncio.TimeoutError as e:
                logger.error("ツール呼び出しタイムアウト", details={"timeout": mcp_config["timeout"]})
                raise TimeoutError(f"ツール呼び出しタイムアウト: {mcp_config['timeout']}秒") from e

    async def get_tools(self, mcp_name: str = None) -> List[Dict[str, Any]]:
        """利用可能なツール一覧を取得

        Args:
            mcp_name: MCP名（指定がない場合は全てのMCP）

        Returns:
            ツール情報のリスト
        """
        tools = []
        for mcp in self.config["remote_mcps"]:
            if mcp_name is None or mcp["name"] == mcp_name:
                mcp_tools = await self._fetch_tools_from_remote(mcp)
                tools.extend(mcp_tools)
        return tools

    async def call_tool(
        self,
        tool: str,
        arguments: Dict[str, Any],
        mcp_name: str = None,
    ) -> Dict[str, Any]:
        """ツールを呼び出す

        Args:
            tool: ツール名
            arguments: ツールの引数
            mcp_name: MCP名（指定がない場合は最初に一致するMCP）

        Returns:
            ツールの実行結果

        Raises:
            ValueError: 指定されたMCPが見つからない
            ToolError: ツール呼び出しに失敗
        """
        for mcp in self.config["remote_mcps"]:
            if mcp_name is None or mcp["name"] == mcp_name:
                return await self._call_remote_tool(mcp, tool, arguments)

        if mcp_name:
            raise ValueError(f"指定されたMCP '{mcp_name}' が見つかりません")
        else:
            raise ValueError("利用可能なMCPが見つかりません") 
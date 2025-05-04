"""Remote MCP Fetcher (RMF) メインモジュール"""

import asyncio
import aiohttp
import yaml
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .exceptions import *
from .logging_config import setup_logger
import uuid
import backoff

@dataclass
class RetryConfig:
    """リトライ設定"""
    max_attempts: int
    initial_delay: float
    max_delay: float

@dataclass
class RemoteMCPConfig:
    """Remote MCP設定"""
    name: str
    base_url: str
    namespace: str
    timeout: int
    retry: RetryConfig
    headers: Optional[Dict[str, str]] = None

def _should_retry_http_error(e):
    """HTTPエラーをリトライすべきかどうかを判定"""
    if isinstance(e, aiohttp.ClientResponseError):
        # 503 Service Unavailableはリトライする
        if e.status == 503:
            return False  # リトライする（Falseを返すとgiveupしない）
        # その他のステータスコードはリトライしない
        return True  # リトライしない（Trueを返すとgiveup）
    
    # その他のエラーはリトライする
    return False

class RemoteMCPFetcher:
    """Remote MCP Fetcherメインクラス"""
    
    def __init__(self, config_path: str):
        """初期化"""
        self.config_path = config_path
        self.logger = setup_logger("rmf", "rmf.log")
        self._load_config()
    
    def _load_config(self) -> None:
        """設定ファイルの読み込み"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            
            # Remote MCP設定の読み込み
            self.remote_mcps = []
            for mcp_config in config.get("remote_mcps", []):
                retry_config = RetryConfig(
                    max_attempts=mcp_config["retry"]["max_attempts"],
                    initial_delay=mcp_config["retry"]["initial_delay"],
                    max_delay=mcp_config["retry"]["max_delay"]
                )
                
                self.remote_mcps.append(RemoteMCPConfig(
                    name=mcp_config["name"],
                    base_url=mcp_config["base_url"],
                    namespace=mcp_config["namespace"],
                    timeout=mcp_config["timeout"],
                    retry=retry_config,
                    headers=mcp_config.get("headers")
                ))
        except Exception as e:
            self.logger.error(f"設定ファイルの読み込みエラー: {str(e)}")
            raise ConfigError(f"設定ファイルの読み込みエラー: {str(e)}")
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError, RMFError),
        max_tries=3,
        giveup=_should_retry_http_error
    )
    async def _fetch_tools_from_remote(self, config: RemoteMCPConfig) -> List[Dict[str, Any]]:
        """Remote MCPからツール一覧を取得"""
        trace_id = str(uuid.uuid4())
        self.logger.info(
            f"ツール一覧の取得開始: {config.name}",
            trace_id=trace_id,
            function="_fetch_tools_from_remote",
            details={
                'mcp_name': config.name,
                'base_url': config.base_url
            }
        )
        
        try:
            timeout = aiohttp.ClientTimeout(total=config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{config.base_url}/tools/list",
                    headers=config.headers
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    tools = data.get("tools", [])
                    self.logger.info(
                        f"ツール一覧の取得成功: {len(tools)}件",
                        trace_id=trace_id,
                        details={
                            'tool_count': len(tools),
                            'status_code': response.status
                        }
                    )
                    return tools
        except asyncio.TimeoutError as e:
            self.logger.error(
                f"ツール一覧の取得タイムアウト: {config.timeout}秒",
                trace_id=trace_id,
                details={
                    'timeout': config.timeout,
                    'exception_type': 'TimeoutError',
                    'exception': str(e)
                }
            )
            raise TimeoutError(f"ツール一覧の取得タイムアウト: {config.timeout}秒")
        except aiohttp.ClientResponseError as e:
            self.logger.error(
                f"ツール一覧の取得エラー: HTTP {e.status}",
                trace_id=trace_id,
                details={
                    'status_code': e.status,
                    'exception_type': e.__class__.__name__,
                    'exception': str(e)
                }
            )
            if e.status == 503:
                # Service Unavailableはリトライ対象なのでRMFErrorを発生させる
                raise RMFError(f"ツール一覧の取得エラー: HTTP {e.status}")
            else:
                # その他のHTTPエラーはリトライしないのでRequestErrorを発生させる
                raise RequestError(f"ツール一覧の取得エラー: HTTP {e.status}")
        except aiohttp.ClientConnectorError as e:
            self.logger.error(
                f"ツール一覧の取得エラー: {str(e)}",
                trace_id=trace_id,
                details={
                    'exception_type': e.__class__.__name__,
                    'exception': str(e)
                }
            )
            raise ConnectionError(f"ツール一覧の取得エラー: {str(e)}")
        except Exception as e:
            self.logger.error(
                f"ツール一覧の取得エラー: {str(e)}",
                trace_id=trace_id,
                details={
                    'exception_type': e.__class__.__name__,
                    'exception': str(e)
                }
            )
            raise RMFError(f"ツール一覧の取得エラー: {str(e)}")
    
    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError, ConnectionError, RMFError),
        max_tries=3,
        giveup=_should_retry_http_error
    )
    async def _call_remote_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        config: Optional[RemoteMCPConfig] = None
    ) -> List[Dict[str, Any]]:
        """Remote MCPのツールを呼び出し"""
        trace_id = str(uuid.uuid4())
        self.logger.info(
            f"ツール呼び出し開始: {tool_name}",
            trace_id=trace_id,
            function="_call_remote_tool",
            details={
                'tool': tool_name,
                'arguments': arguments,
                'mcp_name': config.name if config else self.remote_mcps[0].name
            }
        )
        
        if config is None:
            config = self.remote_mcps[0]
        
        try:
            timeout = aiohttp.ClientTimeout(total=config.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{config.base_url}/tools/call",
                    json={
                        "tool": tool_name,
                        "arguments": arguments
                    },
                    headers=config.headers
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    result = data.get("content", [])
                    self.logger.info(
                        f"ツール呼び出し成功: {tool_name}",
                        trace_id=trace_id,
                        details={
                            'result': data,
                            'status_code': response.status
                        }
                    )
                    return result
        except asyncio.TimeoutError as e:
            self.logger.error(
                f"ツール呼び出しタイムアウト: {tool_name} ({config.timeout}秒)",
                trace_id=trace_id,
                details={
                    'tool': tool_name,
                    'timeout': config.timeout,
                    'exception_type': 'TimeoutError',
                    'exception': str(e)
                }
            )
            raise TimeoutError(f"ツール呼び出しタイムアウト: {tool_name}")
        except aiohttp.ClientResponseError as e:
            self.logger.error(
                f"ツール呼び出し失敗: HTTP {e.status}",
                trace_id=trace_id,
                details={
                    'status_code': e.status,
                    'exception_type': e.__class__.__name__,
                    'exception': str(e),
                    'tool': tool_name
                }
            )
            if e.status == 503:
                # Service Unavailableはリトライ対象なのでRMFErrorを発生させる
                raise RMFError(f"ツール呼び出し失敗: {tool_name} (HTTP {e.status})")
            else:
                # それ以外はリトライしないToolErrorを発生させる
                raise ToolError(f"ツール呼び出し失敗: {tool_name} (HTTP {e.status})")
        except aiohttp.ClientConnectorError as e:
            self.logger.error(
                f"ツール呼び出し接続エラー: {tool_name}",
                trace_id=trace_id,
                details={
                    'tool': tool_name,
                    'exception_type': e.__class__.__name__,
                    'exception': str(e)
                }
            )
            raise ConnectionError(f"ツール呼び出し接続エラー: {tool_name}")
        except Exception as e:
            self.logger.error(
                f"ツール呼び出しエラー: {tool_name}",
                trace_id=trace_id,
                details={
                    'tool': tool_name,
                    'exception_type': e.__class__.__name__,
                    'exception': str(e)
                }
            )
            raise RMFError(f"ツール呼び出しエラー: {tool_name} ({str(e)})")
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """利用可能なツール一覧を取得"""
        all_tools = []
        for config in self.remote_mcps:
            try:
                tools = await self._fetch_tools_from_remote(config)
                all_tools.extend(tools)
            except Exception as e:
                self.logger.error(f"ツール一覧の取得エラー ({config.name}): {str(e)}")
        return all_tools
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ツールを呼び出し"""
        return await self._call_remote_tool(tool_name, arguments) 
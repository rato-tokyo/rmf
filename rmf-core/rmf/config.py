"""設定管理モジュール

環境変数を使用して設定を管理します。
以下の環境変数で設定を制御します：

環境設定:
- RMF_ENV: 実行環境 (production, test, development)

MCP設定:
- RMF_MCP_BASE_URL: MCPのベースURL
- RMF_MCP_TIMEOUT: MCPのタイムアウト時間（秒）
- RMF_MCP_RETRY_MAX_ATTEMPTS: 最大リトライ回数
- RMF_MCP_RETRY_INITIAL_DELAY: 初期リトライ待機時間（秒）
- RMF_MCP_RETRY_MAX_DELAY: 最大リトライ待機時間（秒）

ロギング設定:
- RMF_LOG_LEVEL: ログレベル (INFO, DEBUG, etc.)
- RMF_LOG_FORMAT: ログフォーマット (json)
- RMF_LOG_FILE: ログファイル名

サーバー設定:
- RMF_SERVER_SSE_ENABLED: SSE有効化フラグ
- RMF_SERVER_SSE_RETRY_TIMEOUT: SSEリトライタイムアウト（ミリ秒）
- RMF_SERVER_MAX_CONCURRENT_REQUESTS: 最大同時リクエスト数
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass
import json
import logging
from .errors import ConfigError
from .logging import setup_logging, log_error, get_logger

def safe_int(value: str, default: int, param_name: str) -> int:
    """安全に整数に変換"""
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ConfigError(
            f"Invalid integer value for {param_name}: {value}",
            {'parameter': param_name, 'value': value, 'expected_type': 'integer'}
        )

def safe_float(value: str, default: float, param_name: str) -> float:
    """安全に浮動小数点数に変換"""
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ConfigError(
            f"Invalid float value for {param_name}: {value}",
            {'parameter': param_name, 'value': value, 'expected_type': 'float'}
        )

@dataclass
class RetryConfig:
    """リトライ設定"""
    def __init__(self):
        self.max_attempts = safe_int(
            os.getenv('RMF_MCP_RETRY_MAX_ATTEMPTS', '3'),
            3,
            'RMF_MCP_RETRY_MAX_ATTEMPTS'
        )
        self.initial_delay = safe_float(
            os.getenv('RMF_MCP_RETRY_INITIAL_DELAY', '0.1'),
            0.1,
            'RMF_MCP_RETRY_INITIAL_DELAY'
        )
        self.max_delay = safe_float(
            os.getenv('RMF_MCP_RETRY_MAX_DELAY', '1.0'),
            1.0,
            'RMF_MCP_RETRY_MAX_DELAY'
        )

@dataclass
class MCPConfig:
    """MCP設定"""
    def __init__(self):
        self.name = "Text Processing MCP"
        self.base_url = os.getenv('RMF_MCP_BASE_URL', 'http://localhost:8003')
        self.namespace = "text"
        self.timeout = safe_int(
            os.getenv('RMF_MCP_TIMEOUT', '5'),
            5,
            'RMF_MCP_TIMEOUT'
        )
        self.retry = RetryConfig()
        self.headers = ""

@dataclass
class LoggingConfig:
    """ロギング設定"""
    def __init__(self):
        self.level = os.getenv('RMF_LOG_LEVEL', 'INFO')
        self.format = os.getenv('RMF_LOG_FORMAT', 'json')
        self.file = os.getenv('RMF_LOG_FILE', 'rmf.log')

@dataclass
class ServerConfig:
    """サーバー設定"""
    def __init__(self):
        self.sse_enabled = os.getenv('RMF_SERVER_SSE_ENABLED', 'true').lower() == 'true'
        self.sse_retry_timeout = safe_int(
            os.getenv('RMF_SERVER_SSE_RETRY_TIMEOUT', '3000'),
            3000,
            'RMF_SERVER_SSE_RETRY_TIMEOUT'
        )
        self.max_concurrent_requests = safe_int(
            os.getenv('RMF_SERVER_MAX_CONCURRENT_REQUESTS', '10'),
            10,
            'RMF_SERVER_MAX_CONCURRENT_REQUESTS'
        )

class Config:
    """設定管理クラス"""
    
    def __init__(self):
        self._env = os.getenv('RMF_ENV', 'production')
        self._logger = None
        
        try:
            # 先にロギング設定を初期化（他の設定よりも優先）
            self._logging_config = LoggingConfig()
            
            # ロガーの初期化（他の設定より先に行う）
            self._setup_logger()
            
            # 残りの設定を初期化
            try:
                self._mcp_config = MCPConfig()
            except ConfigError as e:
                # MCPConfig初期化エラーをログ出力
                if self._logger:
                    error_details = {
                        'environment': self._env,
                        'error_code': getattr(e, 'error_code', 'UNKNOWN'),
                        'parameter': getattr(e, 'details', {}).get('parameter', 'UNKNOWN'),
                        'value': getattr(e, 'details', {}).get('value', 'UNKNOWN'),
                        'expected_type': getattr(e, 'details', {}).get('expected_type', 'UNKNOWN')
                    }
                    self._logger.error(str(e), error=e, details=error_details)
                raise
            
            self._server_config = ServerConfig()
            
            # 環境に応じた設定の調整
            self._adjust_config_for_environment()
            
            # 設定読み込み成功のログを出力
            details = {
                'environment': self._env,
                'mcp_base_url': self._mcp_config.base_url,
                'log_level': self._logging_config.level,
                'log_file': self._logging_config.file,
                'server': {
                    'sse_enabled': self._server_config.sse_enabled,
                    'sse_retry_timeout': self._server_config.sse_retry_timeout,
                    'max_concurrent_requests': self._server_config.max_concurrent_requests
                }
            }
            self._logger.info("Configuration loaded successfully", details=details)
        
        except ConfigError as e:
            if self._logger:
                error_details = {
                    'environment': self._env,
                    'error_code': getattr(e, 'error_code', 'UNKNOWN'),
                    'parameter': getattr(e, 'details', {}).get('parameter', 'UNKNOWN'),
                    'value': getattr(e, 'details', {}).get('value', 'UNKNOWN'),
                    'expected_type': getattr(e, 'details', {}).get('expected_type', 'UNKNOWN'),
                    'config_state': {
                        'logging_config': self._logging_config.__dict__ if hasattr(self, '_logging_config') else None,
                        'mcp_config': self._mcp_config.__dict__ if hasattr(self, '_mcp_config') else None,
                        'server_config': self._server_config.__dict__ if hasattr(self, '_server_config') else None
                    }
                }
                self._logger.error(str(e), error=e, details=error_details)
            raise
    
    def _setup_logger(self):
        """ロガーの設定"""
        try:
            # 構造化ロガーを初期化
            logger_config = {
                'level': self._logging_config.level,
                'file': self._logging_config.file,
                'format': self._logging_config.format
            }
            
            # 基本ロガーを初期化
            base_logger = setup_logging(logger_config)
            
            # 環境情報を含むコンテキストを設定
            self._logger = get_logger('rmf', {'environment': self._env})
            
            return self._logger
        except Exception as e:
            import sys
            print(f"ロガー設定エラー: {str(e)}", file=sys.stderr)
            raise
    
    def _adjust_config_for_environment(self):
        """環境に応じて設定を調整"""
        if self._env == 'test':
            self._logging_config.level = 'DEBUG'
            self._logging_config.file = 'rmf_test.log'
            self._server_config.sse_retry_timeout = 1000
            self._server_config.max_concurrent_requests = 5
            self._logger.debug("Test environment configuration applied", details={
                'environment': 'test',
                'log_level': self._logging_config.level,
                'log_file': self._logging_config.file,
                'server_config': {
                    'sse_retry_timeout': self._server_config.sse_retry_timeout,
                    'max_concurrent_requests': self._server_config.max_concurrent_requests
                }
            })
        elif self._env == 'development':
            self._logging_config.level = 'DEBUG'
            self._logging_config.file = 'rmf_dev.log'
            self._server_config.sse_retry_timeout = 1500
            self._server_config.max_concurrent_requests = 3
            self._logger.debug("Development environment configuration applied", details={
                'environment': 'development',
                'log_level': self._logging_config.level,
                'log_file': self._logging_config.file,
                'server_config': {
                    'sse_retry_timeout': self._server_config.sse_retry_timeout,
                    'max_concurrent_requests': self._server_config.max_concurrent_requests
                }
            })
    
    @property
    def remote_mcps(self) -> List[Dict[str, Any]]:
        """リモートMCPの設定を取得"""
        return [{
            'name': self._mcp_config.name,
            'base_url': self._mcp_config.base_url,
            'namespace': self._mcp_config.namespace,
            'timeout': self._mcp_config.timeout,
            'retry': {
                'max_attempts': self._mcp_config.retry.max_attempts,
                'initial_delay': self._mcp_config.retry.initial_delay,
                'max_delay': self._mcp_config.retry.max_delay
            },
            'headers': self._mcp_config.headers
        }]
    
    @property
    def logging(self) -> Dict[str, Any]:
        """ロギングの設定を取得"""
        return {
            'level': self._logging_config.level,
            'format': self._logging_config.format,
            'file': self._logging_config.file
        }
    
    @property
    def server(self) -> Dict[str, Any]:
        """サーバーの設定を取得"""
        return {
            'sse_enabled': self._server_config.sse_enabled,
            'sse_retry_timeout': self._server_config.sse_retry_timeout,
            'max_concurrent_requests': self._server_config.max_concurrent_requests
        }
    
    def get_config(self) -> Dict[str, Any]:
        """全ての設定を取得"""
        return {
            'remote_mcps': self.remote_mcps,
            'logging': self.logging,
            'server': self.server
        }

# シングルトンインスタンス
config = Config() 
"""Remote MCP Framework

複数のRemote MCPサーバーを統合し、単一のインターフェースとして提供するリレー型MCPサーバー。
"""

__version__ = '0.1.0'

# 基本機能を順序立てて明示的にインポート
from .platform import PlatformUtils
from .errors import (
    BaseError, 
    RMFError, 
    ConfigError, 
    TimeoutError, 
    ConnectionError, 
    ToolError, 
    SSEError
)
from .logging import (
    setup_logging, 
    get_logger, 
    log_error, 
    StructuredLogger, 
    LogContext, 
    JSONFormatter, 
    SafeRotatingFileHandler
)
from .config import Config, config
from .env import EnvVarManager, env
from .rmf import RMF

# 公開APIを明示的に列挙
__all__ = [
    # コアクラス
    'RMF',
    
    # エラー関連
    'BaseError',
    'RMFError',
    'ConfigError',
    'TimeoutError',
    'ConnectionError',
    'ToolError',
    'SSEError',
    
    # ロギング関連
    'setup_logging',
    'get_logger',
    'log_error',
    'LogContext',
    'StructuredLogger',
    
    # プラットフォーム
    'PlatformUtils',
    
    # 設定関連
    'Config',
    'config',
    'EnvVarManager',
    'env'
] 
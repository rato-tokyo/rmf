"""Remote MCP Framework

複数のRemote MCPサーバーを統合し、単一のインターフェースとして提供するリレー型MCPサーバー。
"""

__version__ = '0.1.0'

from .config import Config, config
from .errors import RMFError, ConfigError, TimeoutError, ConnectionError, ToolError, SSEError
from .logging import setup_logging, log_error, StructuredLogger, LogContext
from .rmf import RMF

__all__ = [
    'RMF',
    'RMFError',
    'TimeoutError',
    'ConnectionError',
    'ToolError',
    'SSEError',
    'get_logger',
    'LogContext',
    'StructuredLogger'
] 
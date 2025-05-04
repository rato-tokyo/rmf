"""RMFのエラー処理

標準化されたエラー型とエラーハンドリングを提供します。
"""

from typing import Dict, Any, Optional, List, Type
import traceback
import sys
from .logging import StructuredLogger


class BaseError(Exception):
    """RMF基本エラー
    
    すべてのRMF固有エラーの基底クラス
    """
    error_code = 'UNKNOWN'
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


# 統合テストで使用されるRMFErrorとそのサブクラスを追加
class RMFError(BaseError):
    """RMFエラー
    
    RMFライブラリのエラークラス
    """
    error_code = 'RMF'


class TimeoutError(RMFError):
    """タイムアウトエラー
    
    ネットワーク操作のタイムアウト
    """
    error_code = 'TIMEOUT'


class ConnectionError(RMFError):
    """接続エラー
    
    ネットワーク接続に関するエラー
    """
    error_code = 'CONNECTION'


class ConfigError(BaseError):
    """設定エラー
    
    設定の読み込みや解析中に発生するエラー
    """
    error_code = 'CFG'


class NetworkError(BaseError):
    """ネットワークエラー
    
    ネットワーク通信中に発生するエラー
    """
    error_code = 'NET'


class ToolError(BaseError):
    """ツールエラー
    
    リモートツールの呼び出し中に発生するエラー
    """
    error_code = 'TOOL'


class SSEError(BaseError):
    """SSEエラー
    
    SSE（Server-Sent Events）処理中に発生するエラー
    """
    error_code = 'SSE'


class ErrorHandler:
    """エラーハンドリング統一クラス
    
    エラー処理を一元化して、適切なログ出力と回復処理を提供します。
    """
    
    def __init__(self, logger: StructuredLogger):
        """初期化
        
        Args:
            logger: 構造化ロガー
        """
        self.logger = logger
        
        # エラータイプ別のハンドラを登録
        self.handlers = {
            ConfigError: self._handle_config_error,
            NetworkError: self._handle_network_error,
            ToolError: self._handle_tool_error,
            SSEError: self._handle_sse_error,
            Exception: self._handle_generic_error
        }
    
    def handle(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """エラー処理の統一メソッド
        
        Args:
            error: 例外オブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        context = context or {}
        
        # エラータイプに対応するハンドラを検索
        for error_type, handler in self.handlers.items():
            if isinstance(error, error_type):
                return handler(error, context)
        
        # 該当するハンドラがない場合は汎用ハンドラを使用
        return self._handle_generic_error(error, context)
    
    def _handle_config_error(self, error: ConfigError, context: Dict[str, Any]) -> Dict[str, Any]:
        """設定エラー処理
        
        Args:
            error: 設定エラーオブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        details = {
            'error_type': 'ConfigError',
            'error_code': error.error_code,
            **error.details,
            **context
        }
        
        self.logger.error(f"設定エラー: {error.message}", error=error, details=details)
        
        return {
            'success': False,
            'error': str(error),
            'error_code': error.error_code,
            'details': error.details
        }
    
    def _handle_network_error(self, error: NetworkError, context: Dict[str, Any]) -> Dict[str, Any]:
        """ネットワークエラー処理
        
        Args:
            error: ネットワークエラーオブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        details = {
            'error_type': 'NetworkError',
            'error_code': error.error_code,
            'retry_count': context.get('retry_count', 0),
            **error.details,
            **context
        }
        
        self.logger.error(f"ネットワークエラー: {error.message}", error=error, details=details)
        
        # リトライ情報を含めて返す
        return {
            'success': False,
            'error': str(error),
            'error_code': error.error_code,
            'details': error.details,
            'retry_recommended': self._should_retry(error, context)
        }
    
    def _handle_tool_error(self, error: ToolError, context: Dict[str, Any]) -> Dict[str, Any]:
        """ツールエラー処理
        
        Args:
            error: ツールエラーオブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        details = {
            'error_type': 'ToolError',
            'error_code': error.error_code,
            'tool_name': context.get('tool_name', 'unknown'),
            **error.details,
            **context
        }
        
        self.logger.error(f"ツールエラー: {error.message}", error=error, details=details)
        
        return {
            'success': False,
            'error': str(error),
            'error_code': error.error_code,
            'details': error.details
        }
    
    def _handle_sse_error(self, error: SSEError, context: Dict[str, Any]) -> Dict[str, Any]:
        """SSEエラー処理
        
        Args:
            error: SSEエラーオブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        details = {
            'error_type': 'SSEError',
            'error_code': error.error_code,
            **error.details,
            **context
        }
        
        self.logger.error(f"SSEエラー: {error.message}", error=error, details=details)
        
        return {
            'success': False,
            'error': str(error),
            'error_code': error.error_code,
            'details': error.details
        }
    
    def _handle_generic_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """汎用エラー処理
        
        Args:
            error: 例外オブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        error_info = {
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            **context
        }
        
        self.logger.error(f"予期しないエラー: {str(error)}", error=error, details=error_info)
        
        return {
            'success': False,
            'error': str(error),
            'error_code': 'UNKNOWN',
            'details': error_info
        }
    
    def _should_retry(self, error: Exception, context: Dict[str, Any]) -> bool:
        """リトライすべきエラーかどうかを判定
        
        Args:
            error: 例外オブジェクト
            context: エラーコンテキスト
            
        Returns:
            リトライ推奨フラグ
        """
        # リトライ回数をチェック
        retry_count = context.get('retry_count', 0)
        max_retries = context.get('max_retries', 3)
        
        if retry_count >= max_retries:
            return False
        
        # ネットワークエラーは基本的にリトライ
        if isinstance(error, NetworkError):
            return True
        
        # 一時的なエラーとして扱えるものはリトライ
        if isinstance(error, (ConnectionError, TimeoutError)):
            return True
        
        return False


def create_error_handler(logger: StructuredLogger) -> ErrorHandler:
    """エラーハンドラの作成
    
    Args:
        logger: 構造化ロガー
        
    Returns:
        エラーハンドラインスタンス
    """
    return ErrorHandler(logger) 
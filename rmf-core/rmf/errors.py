"""RMFのエラー処理

標準化されたエラー型とエラーハンドリングを提供します。エラー階層：

BaseError (基底クラス)
├── RMFError (RMF関連の基本エラー)
│   ├── TimeoutError (タイムアウト)
│   ├── ConnectionError (接続エラー) 
│   └── ToolError (ツール実行エラー)
├── ConfigError (設定エラー)
├── NetworkError (ネットワークエラー)
└── SSEError (SSEエラー)

各エラータイプにはエラーコードが設定され、詳細情報を辞書形式で保持できます。
"""

from typing import Dict, Any, Optional, List, Type
import traceback
import sys
from .logging import StructuredLogger


class BaseError(Exception):
    """RMF基本エラー
    
    すべてのRMF固有エラーの基底クラス。
    一貫したフォーマットでエラー情報を提供します。
    
    Attributes:
        error_code: エラーコード
        message: エラーメッセージ
        details: エラーの詳細情報
    """
    error_code = 'UNKNOWN'
    
    def __init__(self, message: str, details: Dict[str, Any] = None):
        """初期化
        
        Args:
            message: エラーメッセージ
            details: エラーの詳細情報
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        """文字列表現
        
        Returns:
            エラーコードとメッセージを含む文字列
        """
        return f"[{self.error_code}] {self.message}"


class RMFError(BaseError):
    """RMFエラー
    
    RMFライブラリの一般的なエラークラス。
    特定のエラーカテゴリに分類できないRMF固有のエラーに使用します。
    """
    error_code = 'RMF'


class TimeoutError(RMFError):
    """タイムアウトエラー
    
    ネットワーク操作のタイムアウトを示します。
    主にHTTPリクエストが指定時間内に完了しなかった場合に発生します。
    """
    error_code = 'TIMEOUT'


class ConnectionError(RMFError):
    """接続エラー
    
    ネットワーク接続に関するエラーを示します。
    主にホストへの接続が確立できない場合に発生します。
    """
    error_code = 'CONNECTION'


class ConfigError(BaseError):
    """設定エラー
    
    設定の読み込みや解析中に発生するエラーを示します。
    設定ファイルの形式不正や必須パラメータの欠落時に使用します。
    """
    error_code = 'CFG'


class NetworkError(BaseError):
    """ネットワークエラー
    
    ネットワーク通信中に発生するエラーを示します。
    タイムアウトや接続エラー以外のネットワーク関連エラーに使用します。
    """
    error_code = 'NET'


class ToolError(RMFError):
    """ツールエラー
    
    リモートツールの呼び出し中に発生するエラーを示します。
    主にツールが見つからない場合や実行に失敗した場合に発生します。
    """
    error_code = 'TOOL'


class SSEError(BaseError):
    """SSEエラー
    
    SSE（Server-Sent Events）処理中に発生するエラーを示します。
    イベントストリームの処理に問題がある場合に使用します。
    """
    error_code = 'SSE'


class ErrorHandler:
    """エラーハンドリング統一クラス
    
    エラー処理を一元化して、適切なログ出力と回復処理を提供します。
    各エラータイプに対応する専用ハンドラを持ち、コンテキスト情報を含めて
    エラーを処理します。
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
            TimeoutError: self._handle_timeout_error,
            ConnectionError: self._handle_connection_error,
            RMFError: self._handle_rmf_error,
            BaseError: self._handle_base_error,
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
        
        self.logger.error(f"設定エラー: {error.message}", details=details)
        
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
        
        self.logger.error(f"ネットワークエラー: {error.message}", details=details)
        
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
        
        self.logger.error(f"ツールエラー: {error.message}", details=details)
        
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
        
        self.logger.error(f"SSEエラー: {error.message}", details=details)
        
        return {
            'success': False,
            'error': str(error),
            'error_code': error.error_code,
            'details': error.details
        }
    
    def _handle_timeout_error(self, error: TimeoutError, context: Dict[str, Any]) -> Dict[str, Any]:
        """タイムアウトエラー処理
        
        Args:
            error: タイムアウトエラーオブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        details = {
            'error_type': 'TimeoutError',
            'error_code': error.error_code,
            'timeout': context.get('timeout', 'unknown'),
            **error.details,
            **context
        }
        
        self.logger.error(f"タイムアウトエラー: {error.message}", details=details)
        
        return {
            'success': False,
            'error': str(error),
            'error_code': error.error_code,
            'details': error.details,
            'retry_recommended': self._should_retry(error, context)
        }
    
    def _handle_connection_error(self, error: ConnectionError, context: Dict[str, Any]) -> Dict[str, Any]:
        """接続エラー処理
        
        Args:
            error: 接続エラーオブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        details = {
            'error_type': 'ConnectionError',
            'error_code': error.error_code,
            'host': context.get('host', 'unknown'),
            **error.details,
            **context
        }
        
        self.logger.error(f"接続エラー: {error.message}", details=details)
        
        return {
            'success': False,
            'error': str(error),
            'error_code': error.error_code,
            'details': error.details,
            'retry_recommended': self._should_retry(error, context)
        }
    
    def _handle_rmf_error(self, error: RMFError, context: Dict[str, Any]) -> Dict[str, Any]:
        """RMF一般エラー処理
        
        Args:
            error: RMFエラーオブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        details = {
            'error_type': 'RMFError',
            'error_code': error.error_code,
            **error.details,
            **context
        }
        
        self.logger.error(f"RMFエラー: {error.message}", details=details)
        
        return {
            'success': False,
            'error': str(error),
            'error_code': error.error_code,
            'details': error.details
        }
    
    def _handle_base_error(self, error: BaseError, context: Dict[str, Any]) -> Dict[str, Any]:
        """基本エラー処理
        
        Args:
            error: 基本エラーオブジェクト
            context: エラーコンテキスト
            
        Returns:
            処理結果の辞書
        """
        details = {
            'error_type': error.__class__.__name__,
            'error_code': error.error_code,
            **error.details,
            **context
        }
        
        self.logger.error(f"基本エラー: {error.message}", details=details)
        
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
        
        self.logger.error(f"予期しないエラー: {str(error)}", details=error_info)
        
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
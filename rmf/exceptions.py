"""RMF用の例外クラス"""

class RMFError(Exception):
    """RMF基本例外クラス"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class ConfigError(RMFError):
    """設定エラー"""
    pass

class ConnectionError(RMFError):
    """接続エラー"""
    pass

class RequestError(RMFError):
    """リクエストエラー"""
    pass

class TimeoutError(RMFError):
    """タイムアウトエラー"""
    pass

class ToolError(RMFError):
    """ツール呼び出しエラー"""
    def __init__(self, message: str, tool_name: str = None):
        self.tool_name = tool_name
        super().__init__(message)

class AuthenticationError(RMFError):
    """認証エラー"""
    pass

class NotFoundError(RMFError):
    """リソース未発見エラー"""
    pass

class ValidationError(RMFError):
    """バリデーションエラー"""
    pass 
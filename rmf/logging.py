"""ロギング設定モジュール

structlogを使用して構造化ログを出力します。
すべてのログはJSON形式で出力され、以下の情報が自動的に付与されます：
- timestamp: ログ出力時刻
- level: ログレベル
- logger: ロガー名
- function: 関数名
- trace_id: トレースID（リクエストの追跡用）
"""

import sys
import uuid
import logging
import structlog
from typing import Any, Dict, Optional
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="RMF",
    settings_files=["settings.toml"],
    environments=True,
    load_dotenv=True,
    default_settings={
        "logging": {
            "level": "INFO",
            "format": "json",
            "file": "rmf.log"
        }
    }
)

def generate_trace_id() -> str:
    """新しいトレースIDを生成"""
    return str(uuid.uuid4())

def add_trace_id(logger: structlog.BoundLogger, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """トレースIDをログに追加"""
    if "trace_id" not in event_dict:
        event_dict["trace_id"] = generate_trace_id()
    return event_dict

def setup_logging() -> None:
    """ロギングの設定をセットアップ"""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.logging.level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            add_trace_id,
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str = None) -> structlog.BoundLogger:
    """構造化ロガーを取得

    Args:
        name: ロガー名（デフォルトはモジュール名）

    Returns:
        構造化ロガーインスタンス
    """
    return structlog.get_logger(name)

class LogContext:
    """ログコンテキストマネージャー

    with文で使用することで、ブロック内のすべてのログに
    自動的にコンテキスト情報を付与します。

    Example:
        with LogContext(function="process_request", user_id="123"):
            logger.info("リクエスト処理開始")
            # ログには function="process_request", user_id="123" が自動的に付与される
    """

    def __init__(self, **context):
        self.context = context
        self.previous_context = None

    def __enter__(self):
        # 現在のコンテキストを保存
        self.previous_context = structlog.contextvars.get_contextvars()
        # 新しいコンテキストを設定
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 以前のコンテキストを復元
        structlog.contextvars.clear_contextvars()
        if self.previous_context:
            structlog.contextvars.bind_contextvars(**self.previous_context)
        return None

# デフォルトのロギング設定を適用
setup_logging() 
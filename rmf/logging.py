"""RMFのロギング機能

JSON形式のログ出力とログローテーションを提供します。
プラットフォーム固有の動作に対応し、特にWindows環境でのファイル操作に関する問題に対応します。
"""

import logging
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict, Any, Optional
import os
import sys
import time
from pathlib import Path
from .platform import PlatformUtils


class JSONFormatter(logging.Formatter):
    """JSON形式のログフォーマッタ"""
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式に変換"""
        # 基本的なログデータを構築
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'details': {}  # デフォルトで空の辞書を設定
        }
        
        # detailsの取得と処理
        if hasattr(record, 'details'):
            if isinstance(record.details, dict):
                log_data['details'] = record.details
        elif hasattr(record, 'extra'):
            if isinstance(record.extra, dict) and 'details' in record.extra:
                details = record.extra.get('details', {})
                if isinstance(details, dict):
                    log_data['details'] = details
        
        # エラー情報の追加
        if record.exc_info:
            log_data['error'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        try:
            return json.dumps(log_data, ensure_ascii=False)
        except Exception as e:
            # JSON変換に失敗した場合のフォールバック
            fallback_data = {
                'timestamp': self.formatTime(record),
                'level': 'ERROR',
                'message': 'Failed to format log message',
                'error': str(e),
                'original_message': record.getMessage(),
                'details': {}
            }
            return json.dumps(fallback_data, ensure_ascii=False)


class SafeRotatingFileHandler(RotatingFileHandler):
    """プラットフォーム対応のRotatingFileHandler
    
    特にWindows環境でのファイルロック問題に対応します。
    """
    
    def __init__(self, filename, **kwargs):
        """初期化
        
        Args:
            filename: ログファイルのパス
            **kwargs: RotatingFileHandlerの追加パラメータ
        """
        # ファイルパスを正規化
        filename = PlatformUtils.get_safe_path(filename)
        
        # 親ディレクトリが存在することを確認
        PlatformUtils.ensure_directory(Path(filename).parent)
        
        # Windows環境での問題を回避するため、mode='a'を明示的に指定
        kwargs['mode'] = kwargs.get('mode', 'a')
        kwargs['encoding'] = kwargs.get('encoding', 'utf-8')
        kwargs['delay'] = False  # 常に即時オープン
        
        super().__init__(filename, **kwargs)
        
        # Windows環境でのファイルロックを確実に解放するため
        self.terminator = '\n'
    
    def emit(self, record):
        """ログレコードの出力
        
        Args:
            record: ログレコード
        """
        try:
            # ストリームが存在しない場合は開く
            if self.stream is None:
                self.stream = self._open()
            
            # レコードをフォーマット
            msg = self.format(record)
            stream = self.stream
            
            try:
                # エンコーディングに応じた書き込み
                if getattr(stream, 'encoding', None) is not None:
                    stream.write(msg + self.terminator)
                else:
                    stream.write(bytes(msg + self.terminator, 'utf-8'))
                
                # 即時フラッシュしてディスクに書き込む
                self.flush()
                
                # Windows環境では確実に書き込まれるよう追加措置
                if PlatformUtils.is_windows() and hasattr(os, 'fsync') and hasattr(stream, 'fileno'):
                    try:
                        os.fsync(stream.fileno())
                    except Exception:
                        pass
                
            except Exception:
                self.handleError(record)
            
        except Exception:
            self.handleError(record)
    
    def close(self):
        """ファイルハンドラのクローズ処理"""
        if self.stream:
            try:
                self.flush()
                if hasattr(self.stream, 'fileno'):
                    try:
                        os.fsync(self.stream.fileno())
                    except Exception:
                        pass
                self.stream.close()
            except Exception:
                pass
            finally:
                self.stream = None


class LoggingManager:
    """ロギング管理クラス
    
    ロギングの初期化と管理を担当します。
    """
    
    @staticmethod
    def configure(config: Dict[str, Any]) -> logging.Logger:
        """ロギングの設定
        
        Args:
            config: ロギング設定
                - level: ログレベル
                - file: ログファイル名
                - format: ログフォーマット（json固定）
        
        Returns:
            設定されたロガーインスタンス
        """
        logger_name = 'rmf'
        logger = logging.getLogger(logger_name)
        
        # ログレベル設定
        log_level = getattr(logging, config['level'], logging.INFO)
        logger.setLevel(log_level)
        
        # 既存のハンドラをクリア
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)
        
        try:
            # ログファイルのパスを正規化
            log_file = Path(config['file']).resolve()
            
            # ディレクトリが存在しない場合は作成
            PlatformUtils.ensure_directory(log_file.parent)
            
            # ファイルハンドラの設定
            file_handler = SafeRotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(JSONFormatter())
            logger.addHandler(file_handler)
            
            # 開発環境ではコンソールハンドラも追加
            if os.getenv('RMF_ENV') in ['development', 'test']:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(JSONFormatter())
                logger.addHandler(console_handler)
            
            return logger
            
        except Exception as e:
            # セットアップに失敗した場合は最低限のコンソールハンドラを設定
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
            logger.addHandler(console_handler)
            
            logger.error(f"ロギング設定エラー: {str(e)}", exc_info=True)
            return logger


class StructuredLogger:
    """構造化ロギング用クラス
    
    詳細情報（details）付きのログを出力します。
    """
    
    def __init__(self, logger, context=None):
        """初期化
        
        Args:
            logger: 基本のロガーインスタンス
            context: コンテキスト情報（すべてのログに付加される）
        """
        self.logger = logger
        self.context = context or {}
    
    def _prepare_extras(self, details=None, **kwargs):
        """extra情報の準備
        
        Args:
            details: 詳細情報
            **kwargs: その他のパラメータ
        
        Returns:
            準備されたextra情報
        """
        combined_details = self.context.copy()
        if details:
            combined_details.update(details)
        
        # 既にextraが存在する場合は、それを更新
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # RecordFactory方式ではなく、extra経由でdetailsを渡す
        kwargs['extra']['details'] = combined_details
        
        return kwargs
    
    def debug(self, message, details=None, **kwargs):
        """DEBUGログの出力
        
        Args:
            message: ログメッセージ
            details: 詳細情報
            **kwargs: その他のパラメータ
        """
        kwargs = self._prepare_extras(details, **kwargs)
        self.logger.debug(message, **kwargs)
    
    def info(self, message, details=None, **kwargs):
        """INFOログの出力
        
        Args:
            message: ログメッセージ
            details: 詳細情報
            **kwargs: その他のパラメータ
        """
        kwargs = self._prepare_extras(details, **kwargs)
        self.logger.info(message, **kwargs)
    
    def warning(self, message, details=None, **kwargs):
        """WARNINGログの出力
        
        Args:
            message: ログメッセージ
            details: 詳細情報
            **kwargs: その他のパラメータ
        """
        kwargs = self._prepare_extras(details, **kwargs)
        self.logger.warning(message, **kwargs)
    
    def error(self, message, error=None, details=None, **kwargs):
        """ERRORログの出力
        
        Args:
            message: ログメッセージ
            error: 例外オブジェクト
            details: 詳細情報
            **kwargs: その他のパラメータ
        """
        # エラー情報を詳細に追加
        error_details = details or {}
        if error:
            error_details.update({
                'error_type': error.__class__.__name__,
                'error_message': str(error)
            })
        
        kwargs = self._prepare_extras(error_details, **kwargs)
        self.logger.error(message, exc_info=error is not None, **kwargs)
    
    def critical(self, message, error=None, details=None, **kwargs):
        """CRITICALログの出力
        
        Args:
            message: ログメッセージ
            error: 例外オブジェクト
            details: 詳細情報
            **kwargs: その他のパラメータ
        """
        # エラー情報を詳細に追加
        error_details = details or {}
        if error:
            error_details.update({
                'error_type': error.__class__.__name__,
                'error_message': str(error)
            })
        
        kwargs = self._prepare_extras(error_details, **kwargs)
        self.logger.critical(message, exc_info=error is not None, **kwargs)


class LogContext:
    """ロギングコンテキストマネージャ
    
    with文で使用し、ログに一時的なコンテキスト情報を追加します。
    """
    
    def __init__(self, test_name=None, function_name=None, **kwargs):
        """初期化
        
        Args:
            test_name: テスト名
            function_name: 関数名
            **kwargs: その他のコンテキスト情報
        """
        self.context = {'test_name': test_name} if test_name else {}
        if function_name:
            self.context['function_name'] = function_name
        self.context.update(kwargs)
        
        # 元のロギングコンテキストを保存するため変数
        self._original_context = None
        self._previous_loggers = {}
    
    def __enter__(self):
        """コンテキスト開始処理
        
        現在のスレッドに関連するすべてのロガーのコンテキストを一時的に変更します
        """
        # rmfロガーと関連ロガーを取得
        loggers = [logging.getLogger('rmf')]
        loggers.extend([logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith('rmf.')])
        
        # 元のコンテキストを保存して新しいコンテキストを設定
        for logger in loggers:
            if hasattr(logger, 'context'):
                structured_logger = logger
            else:
                # 通常のロガーからStructuredLoggerを取得できるか試みる
                structured_logger = None
                for handler in logger.handlers:
                    if hasattr(handler, 'logger') and isinstance(handler.logger, StructuredLogger):
                        structured_logger = handler.logger
                        break
            
            if structured_logger:
                self._previous_loggers[logger.name] = structured_logger
                
                # 元のコンテキストを保存
                original_context = structured_logger.context.copy()
                
                # 新しいコンテキストを設定
                structured_logger.context.update(self.context)
                
                # 元に戻すために保存
                if not self._original_context:
                    self._original_context = {}
                self._original_context[logger.name] = original_context
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキスト終了処理
        
        変更したコンテキストを元に戻します
        """
        if self._original_context:
            for logger_name, original_context in self._original_context.items():
                if logger_name in self._previous_loggers:
                    # コンテキストを元に戻す
                    self._previous_loggers[logger_name].context = original_context
        
        return False  # 例外を再スローする


def setup_logging(config: Dict[str, Any]) -> StructuredLogger:
    """ロギングの設定
    
    Args:
        config: ロギング設定
            - level: ログレベル
            - file: ログファイル名
            - format: ログフォーマット（json固定）
    
    Returns:
        構造化ロガーインスタンス
    """
    logger = LoggingManager.configure(config)
    return StructuredLogger(logger)


def get_logger(name='rmf', context=None) -> StructuredLogger:
    """詳細情報を含むロガーを取得
    
    Args:
        name: ロガー名
        context: 基本的な詳細情報
    
    Returns:
        構造化ロガーインスタンス
    """
    logger = logging.getLogger(name)
    return StructuredLogger(logger, context)


def log_error(logger, error: Exception, details: Dict[str, Any] = None):
    """エラーログの出力
    
    Args:
        logger: ロガーインスタンス
        error: エラーオブジェクト
        details: 追加情報
    """
    if isinstance(logger, StructuredLogger):
        logger.error(str(error), error=error, details=details)
    else:
        if details is None:
            details = {}
        
        error_details = {
            'error_type': error.__class__.__name__,
            'error_message': str(error),
            **details
        }
        
        logger.error(
            str(error),
            exc_info=True,
            extra={'details': error_details}
        ) 
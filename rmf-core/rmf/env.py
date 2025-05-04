"""環境変数管理

環境変数の読み込みと変換を管理します。
"""

import os
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic, Callable, Type, cast
from .errors import ConfigError


T = TypeVar('T')


class EnvVarManager:
    """環境変数管理クラス
    
    環境変数の取得と型変換を行います。
    """
    
    def __init__(self, prefix: str = 'RMF_'):
        """初期化
        
        Args:
            prefix: 環境変数のプレフィックス
        """
        self.prefix = prefix
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """環境変数を取得
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
            default: デフォルト値
            
        Returns:
            環境変数の値またはデフォルト値
        """
        full_key = f"{self.prefix}{key}"
        return os.environ.get(full_key, default)
    
    def get_required(self, key: str) -> str:
        """必須の環境変数を取得
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
            
        Returns:
            環境変数の値
            
        Raises:
            ConfigError: 環境変数が設定されていない場合
        """
        full_key = f"{self.prefix}{key}"
        value = os.environ.get(full_key)
        
        if value is None:
            raise ConfigError(
                f"Required environment variable {full_key} is not set",
                {'parameter': full_key}
            )
        
        return value
    
    def get_int(self, key: str, default: int) -> int:
        """整数値の環境変数を取得
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
            default: デフォルト値
            
        Returns:
            整数に変換された環境変数の値またはデフォルト値
            
        Raises:
            ConfigError: 環境変数の値が整数に変換できない場合
        """
        full_key = f"{self.prefix}{key}"
        value = os.environ.get(full_key)
        
        if value is None:
            return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            raise ConfigError(
                f"Invalid integer value for {full_key}: {value}",
                {'parameter': full_key, 'value': value, 'expected_type': 'integer'}
            )
    
    def get_float(self, key: str, default: float) -> float:
        """浮動小数点値の環境変数を取得
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
            default: デフォルト値
            
        Returns:
            浮動小数点数に変換された環境変数の値またはデフォルト値
            
        Raises:
            ConfigError: 環境変数の値が浮動小数点数に変換できない場合
        """
        full_key = f"{self.prefix}{key}"
        value = os.environ.get(full_key)
        
        if value is None:
            return default
        
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ConfigError(
                f"Invalid float value for {full_key}: {value}",
                {'parameter': full_key, 'value': value, 'expected_type': 'float'}
            )
    
    def get_bool(self, key: str, default: bool) -> bool:
        """真偽値の環境変数を取得
        
        Trueとして扱う値: 'true', 'yes', '1', 'y', 'on'（大文字小文字は区別しない）
        Falseとして扱う値: 'false', 'no', '0', 'n', 'off'（大文字小文字は区別しない）
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
            default: デフォルト値
            
        Returns:
            真偽値に変換された環境変数の値またはデフォルト値
            
        Raises:
            ConfigError: 環境変数の値が真偽値に変換できない場合
        """
        full_key = f"{self.prefix}{key}"
        value = os.environ.get(full_key)
        
        if value is None:
            return default
        
        true_values = ['true', 'yes', '1', 'y', 'on']
        false_values = ['false', 'no', '0', 'n', 'off']
        
        value_lower = value.lower()
        
        if value_lower in true_values:
            return True
        elif value_lower in false_values:
            return False
        else:
            raise ConfigError(
                f"Invalid boolean value for {full_key}: {value}",
                {'parameter': full_key, 'value': value, 'expected_type': 'boolean'}
            )
    
    def get_list(self, key: str, default: List[str], separator: str = ',') -> List[str]:
        """リスト形式の環境変数を取得
        
        カンマ区切りの値をリストに変換します。
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
            default: デフォルト値
            separator: リスト要素の区切り文字
            
        Returns:
            リストに変換された環境変数の値またはデフォルト値
        """
        full_key = f"{self.prefix}{key}"
        value = os.environ.get(full_key)
        
        if value is None:
            return default
        
        # 空の値のときは空リストを返す
        if not value.strip():
            return []
        
        # カンマ区切りの値をリストに変換
        return [item.strip() for item in value.split(separator) if item.strip()]
    
    def get_dict(self, key: str, default: Dict[str, str], item_separator: str = ',', key_value_separator: str = '=') -> Dict[str, str]:
        """辞書形式の環境変数を取得
        
        カンマ区切りのkey=value形式の値を辞書に変換します。
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
            default: デフォルト値
            item_separator: 項目の区切り文字
            key_value_separator: キーと値の区切り文字
            
        Returns:
            辞書に変換された環境変数の値またはデフォルト値
            
        Raises:
            ConfigError: 環境変数の値が辞書形式に変換できない場合
        """
        full_key = f"{self.prefix}{key}"
        value = os.environ.get(full_key)
        
        if value is None:
            return default
        
        # 空の値のときは空辞書を返す
        if not value.strip():
            return {}
        
        result = {}
        
        try:
            # カンマ区切りの値を処理
            for item in value.split(item_separator):
                item = item.strip()
                if not item:
                    continue
                
                # key=value形式に分割
                if key_value_separator not in item:
                    raise ValueError(f"Invalid key-value pair: {item}")
                
                k, v = item.split(key_value_separator, 1)
                result[k.strip()] = v.strip()
            
            return result
        
        except Exception as e:
            raise ConfigError(
                f"Invalid dictionary format for {full_key}: {value}",
                {'parameter': full_key, 'value': value, 'expected_type': 'dictionary', 'error': str(e)}
            )
    
    def set(self, key: str, value: Any) -> None:
        """環境変数を設定
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
            value: 設定する値
        """
        full_key = f"{self.prefix}{key}"
        os.environ[full_key] = str(value)
    
    def clear(self, key: str) -> None:
        """環境変数をクリア
        
        Args:
            key: 環境変数名（プレフィックスを除く部分）
        """
        full_key = f"{self.prefix}{key}"
        if full_key in os.environ:
            del os.environ[full_key]
    
    def clear_all(self) -> None:
        """プレフィックスに一致するすべての環境変数をクリア"""
        for key in list(os.environ.keys()):
            if key.startswith(self.prefix):
                del os.environ[key]


# シングルトンインスタンス
env = EnvVarManager() 
"""設定管理モジュール

環境変数RMF_ENVを使用して設定を切り替えます：
- production: 本番環境（デフォルト）
- test: テスト環境
- development: 開発環境
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """設定管理クラス"""
    
    DEFAULT_CONFIG_PATH = "config.yaml"
    ENV_VAR_NAME = "RMF_ENV"
    
    def __init__(self):
        self.env = os.getenv(self.ENV_VAR_NAME, "production")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """環境に応じた設定をロードする"""
        base_config = self._load_yaml(self.DEFAULT_CONFIG_PATH)
        
        # 環境固有の設定をマージ
        env_config_path = f"config_{self.env}.yaml"
        if Path(env_config_path).exists():
            env_config = self._load_yaml(env_config_path)
            base_config = self._deep_merge(base_config, env_config)
        
        # 環境変数でオーバーライド
        self._override_from_env(base_config)
        return base_config
    
    @staticmethod
    def _load_yaml(path: str) -> Dict[str, Any]:
        """YAMLファイルをロードする"""
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """辞書を再帰的にマージする"""
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def _override_from_env(self, config: Dict[str, Any]) -> None:
        """環境変数で設定をオーバーライドする
        
        環境変数の形式: RMF_<セクション>_<キー>=値
        例: RMF_LOGGING_LEVEL=DEBUG
        """
        prefix = "RMF_"
        for env_var, value in os.environ.items():
            if env_var.startswith(prefix):
                parts = env_var[len(prefix):].lower().split('_')
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
    
    def get_config(self) -> Dict[str, Any]:
        """現在の設定を取得する"""
        return self.config.copy()

# シングルトンインスタンス
config_manager = ConfigManager() 
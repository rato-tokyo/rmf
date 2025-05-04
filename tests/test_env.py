"""環境変数管理のテスト"""

import pytest
from rmf.env import EnvVarManager
from rmf.errors import ConfigError


@pytest.fixture
def env_manager():
    """テスト用の環境変数マネージャー"""
    return EnvVarManager(prefix='TEST_')


def test_get_basic(env_manager, monkeypatch):
    """基本的な環境変数の取得テスト"""
    monkeypatch.setenv('TEST_BASIC', 'value')
    assert env_manager.get('BASIC') == 'value'
    assert env_manager.get('NOT_EXISTS') is None
    assert env_manager.get('NOT_EXISTS', 'default') == 'default'


def test_get_required(env_manager, monkeypatch):
    """必須環境変数の取得テスト"""
    monkeypatch.setenv('TEST_REQUIRED', 'value')
    assert env_manager.get_required('REQUIRED') == 'value'
    
    with pytest.raises(ConfigError) as exc_info:
        env_manager.get_required('NOT_EXISTS')
    assert 'Required environment variable' in str(exc_info.value)


def test_get_int(env_manager, monkeypatch):
    """整数値の環境変数取得テスト"""
    monkeypatch.setenv('TEST_INT', '123')
    assert env_manager.get_int('INT', 0) == 123
    assert env_manager.get_int('NOT_EXISTS', 456) == 456
    
    monkeypatch.setenv('TEST_INVALID_INT', 'not_a_number')
    with pytest.raises(ConfigError) as exc_info:
        env_manager.get_int('INVALID_INT', 0)
    assert 'Invalid integer value' in str(exc_info.value)


def test_get_float(env_manager, monkeypatch):
    """浮動小数点値の環境変数取得テスト"""
    monkeypatch.setenv('TEST_FLOAT', '123.45')
    assert env_manager.get_float('FLOAT', 0.0) == 123.45
    assert env_manager.get_float('NOT_EXISTS', 456.78) == 456.78
    
    monkeypatch.setenv('TEST_INVALID_FLOAT', 'not_a_number')
    with pytest.raises(ConfigError) as exc_info:
        env_manager.get_float('INVALID_FLOAT', 0.0)
    assert 'Invalid float value' in str(exc_info.value)


def test_get_bool(env_manager, monkeypatch):
    """真偽値の環境変数取得テスト"""
    # True値のテスト
    for true_value in ['true', 'yes', '1', 'y', 'on', 'TRUE', 'YES', 'Y', 'ON']:
        monkeypatch.setenv('TEST_BOOL', true_value)
        assert env_manager.get_bool('BOOL', False) is True
    
    # False値のテスト
    for false_value in ['false', 'no', '0', 'n', 'off', 'FALSE', 'NO', 'N', 'OFF']:
        monkeypatch.setenv('TEST_BOOL', false_value)
        assert env_manager.get_bool('BOOL', True) is False
    
    # 無効な値のテスト
    monkeypatch.setenv('TEST_INVALID_BOOL', 'invalid')
    with pytest.raises(ConfigError) as exc_info:
        env_manager.get_bool('INVALID_BOOL', False)
    assert 'Invalid boolean value' in str(exc_info.value)


def test_get_list(env_manager, monkeypatch):
    """リスト形式の環境変数取得テスト"""
    monkeypatch.setenv('TEST_LIST', 'item1,item2,item3')
    assert env_manager.get_list('LIST', []) == ['item1', 'item2', 'item3']
    
    # 空白を含む値のテスト
    monkeypatch.setenv('TEST_LIST_SPACES', ' item1 , item2 , item3 ')
    assert env_manager.get_list('LIST_SPACES', []) == ['item1', 'item2', 'item3']
    
    # カスタム区切り文字のテスト
    monkeypatch.setenv('TEST_LIST_CUSTOM', 'item1;item2;item3')
    assert env_manager.get_list('LIST_CUSTOM', [], separator=';') == ['item1', 'item2', 'item3']
    
    # 空の値のテスト
    monkeypatch.setenv('TEST_LIST_EMPTY', '')
    assert env_manager.get_list('LIST_EMPTY', ['default']) == []
    
    # 存在しない値のテスト
    assert env_manager.get_list('NOT_EXISTS', ['default']) == ['default']


def test_get_dict(env_manager, monkeypatch):
    """辞書形式の環境変数取得テスト"""
    monkeypatch.setenv('TEST_DICT', 'key1=value1,key2=value2')
    assert env_manager.get_dict('DICT', {}) == {'key1': 'value1', 'key2': 'value2'}
    
    # 空白を含む値のテスト
    monkeypatch.setenv('TEST_DICT_SPACES', ' key1 = value1 , key2 = value2 ')
    assert env_manager.get_dict('DICT_SPACES', {}) == {'key1': 'value1', 'key2': 'value2'}
    
    # カスタム区切り文字のテスト
    monkeypatch.setenv('TEST_DICT_CUSTOM', 'key1=value1;key2=value2')
    assert env_manager.get_dict('DICT_CUSTOM', {}, item_separator=';') == {'key1': 'value1', 'key2': 'value2'}
    
    # 無効な形式のテスト
    monkeypatch.setenv('TEST_INVALID_DICT', 'invalid_format')
    with pytest.raises(ConfigError) as exc_info:
        env_manager.get_dict('INVALID_DICT', {})
    assert 'Invalid dictionary format' in str(exc_info.value)


def test_set_and_clear(env_manager):
    """環境変数の設定とクリアのテスト"""
    # 値の設定
    env_manager.set('SET_TEST', 'test_value')
    assert env_manager.get('SET_TEST') == 'test_value'
    
    # 値のクリア
    env_manager.clear('SET_TEST')
    assert env_manager.get('SET_TEST') is None
    
    # 全値のクリア
    env_manager.set('TEST1', 'value1')
    env_manager.set('TEST2', 'value2')
    env_manager.clear_all()
    assert env_manager.get('TEST1') is None
    assert env_manager.get('TEST2') is None 
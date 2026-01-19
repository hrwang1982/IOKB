"""
基础测试用例
"""

def test_import():
    """测试模块导入"""
    from app import __version__
    assert __version__ == "0.1.0"


def test_config():
    """测试配置加载"""
    from app.config import settings
    assert settings.app_name == "SKB"

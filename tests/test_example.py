"""
示例测试文件
"""

def test_addition():
    """测试加法"""
    assert 1 + 1 == 2


def test_subtraction():
    """测试减法"""
    assert 3 - 1 == 2


def test_multiplication():
    """测试乘法"""
    assert 2 * 3 == 6


def test_division():
    """测试除法"""
    assert 6 / 2 == 3


def test_failure():
    """这个测试会失败"""
    assert 1 == 2, "这个测试应该失败"


def test_skip():
    """这个测试会被跳过"""
    import pytest
    pytest.skip("跳过这个测试")


class TestClass:
    """测试类"""
    
    def test_class_method(self):
        """类方法测试"""
        assert "hello".upper() == "HELLO"
    
    def test_another_method(self):
        """另一个类方法测试"""
        assert "world".title() == "World"
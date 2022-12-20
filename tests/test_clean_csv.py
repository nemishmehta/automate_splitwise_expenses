from src.main import app


def test_placeholder():
    assert app.placeholder() == "Hello"

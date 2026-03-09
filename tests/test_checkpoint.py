from unittest.mock import patch
from core.checkpoint import HumanCheckpoint

def test_ask_returns_user_input():
    cp = HumanCheckpoint()
    with patch("builtins.input", return_value="B를 선택"):
        result = cp.ask("어떤 아이디어를 선택하시겠습니까?")
    assert result == "B를 선택"

def test_confirm_yes():
    cp = HumanCheckpoint()
    with patch("builtins.input", return_value="y"):
        result = cp.confirm("계속하시겠습니까?")
    assert result is True

def test_confirm_no():
    cp = HumanCheckpoint()
    with patch("builtins.input", return_value="n"):
        result = cp.confirm("계속하시겠습니까?")
    assert result is False

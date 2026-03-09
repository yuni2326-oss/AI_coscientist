import pytest
from unittest.mock import patch, MagicMock
from core.claude_runner import ClaudeRunner

def test_generate_returns_string():
    runner = ClaudeRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="Claude 응답 텍스트",
            returncode=0
        )
        result = runner.generate("테스트 프롬프트")
    assert isinstance(result, str)
    assert len(result) > 0

def test_generate_raises_on_error():
    runner = ClaudeRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="",
            returncode=1,
            stderr="error"
        )
        with pytest.raises(RuntimeError):
            runner.generate("프롬프트")

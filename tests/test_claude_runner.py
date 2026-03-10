import pytest
from unittest.mock import patch, MagicMock
from core.claude_runner import ClaudeRunner


def test_generate_returns_string():
    runner = ClaudeRunner()
    with patch("core.claude_runner._anthropic_available", False), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="Claude 응답 텍스트", returncode=0)
        result = runner.generate("테스트 프롬프트")
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_raises_on_error():
    runner = ClaudeRunner()
    with patch("core.claude_runner._anthropic_available", False), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=1, stderr="error")
        with pytest.raises(RuntimeError):
            runner.generate("프롬프트")


def test_generate_via_sdk():
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="SDK 응답")]
    )
    runner = ClaudeRunner()
    with patch("core.claude_runner._anthropic_available", True), \
         patch("core.claude_runner.anthropic.Anthropic", return_value=mock_client):
        result = runner.generate("테스트")
    assert result == "SDK 응답"

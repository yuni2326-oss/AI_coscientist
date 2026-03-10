import pytest
from unittest.mock import patch, MagicMock
from core.claude_runner import ClaudeRunner


def _mock_anthropic(response_text: str):
    """Anthropic SDK 응답 mock 헬퍼"""
    mock_client = MagicMock()
    mock_content = MagicMock()
    mock_content.text = response_text
    mock_client.messages.create.return_value = MagicMock(content=[mock_content])
    return mock_client


def test_generate_returns_string():
    runner = ClaudeRunner()
    with patch("core.claude_runner.anthropic.Anthropic", return_value=_mock_anthropic("Claude 응답 텍스트")):
        result = runner.generate("테스트 프롬프트")
    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_raises_on_error():
    runner = ClaudeRunner()
    with patch("core.claude_runner.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value.messages.create.side_effect = RuntimeError("API error")
        with pytest.raises(RuntimeError):
            runner.generate("프롬프트")


def test_generate_falls_back_to_cli_when_sdk_unavailable():
    runner = ClaudeRunner()
    with patch("core.claude_runner._anthropic_available", False), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="CLI 응답", returncode=0)
        result = runner.generate("테스트")
    assert result == "CLI 응답"

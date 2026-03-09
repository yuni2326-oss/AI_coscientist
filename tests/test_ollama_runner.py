import pytest
from unittest.mock import patch, MagicMock
from core.ollama_runner import OllamaRunner

def test_generate_returns_string():
    runner = OllamaRunner()
    with patch("core.ollama_runner.ollama.chat") as mock_chat:
        mock_chat.return_value = {"message": {"content": "테스트 응답"}}
        result = runner.generate("테스트 프롬프트")
    assert isinstance(result, str)
    assert len(result) > 0

def test_generate_passes_prompt():
    runner = OllamaRunner()
    with patch("core.ollama_runner.ollama.chat") as mock_chat:
        mock_chat.return_value = {"message": {"content": "응답"}}
        runner.generate("내 프롬프트")
    call_args = mock_chat.call_args
    assert "내 프롬프트" in str(call_args)

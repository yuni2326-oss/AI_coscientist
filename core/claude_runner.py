import subprocess
from config import settings

try:
    import anthropic
    _anthropic_available = True
except ImportError:
    _anthropic_available = False


class ClaudeRunner:
    def generate(self, prompt: str) -> str:
        if _anthropic_available:
            return self._generate_via_sdk(prompt)
        return self._generate_via_cli(prompt)

    def _generate_via_sdk(self, prompt: str) -> str:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

    def _generate_via_cli(self, prompt: str) -> str:
        result = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=settings.claude_timeout,
            encoding="utf-8"
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr}")
        return result.stdout.strip()

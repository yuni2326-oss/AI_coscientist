import subprocess
from config import settings

class ClaudeRunner:
    def generate(self, prompt: str) -> str:
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

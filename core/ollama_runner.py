import ollama
from config import settings

class OllamaRunner:
    def __init__(self, model: str = None):
        self.model = model or settings.ollama_model

    def generate(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = ollama.chat(
            model=self.model,
            messages=messages
        )
        return response["message"]["content"]

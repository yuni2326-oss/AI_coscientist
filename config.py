from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    claude_timeout: int = 600
    max_ideas: int = 5
    output_dir: str = "outputs"

    class Config:
        env_file = ".env"

settings = Settings()

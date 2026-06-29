from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    ollama_model: str = "gemma4:26b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_ctx: int = 16384
    ollama_temperature: float = 0.7
    claude_timeout: int = 600
    max_ideas: int = 5
    output_dir: str = "outputs"
    semantic_scholar_api_key: str = ""

settings = Settings()

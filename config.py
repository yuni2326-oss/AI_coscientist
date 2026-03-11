from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    ollama_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"
    ollama_num_ctx: int = 12288
    ollama_temperature: float = 0.7
    claude_timeout: int = 600
    max_ideas: int = 5
    output_dir: str = "outputs"

settings = Settings()

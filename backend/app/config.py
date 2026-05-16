from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    postgres_dsn: str = "postgresql://postgres:postgres@localhost:5432/biomed"

    redis_url: str = "redis://localhost:6379/0"

    ingest_rate_limit: float = 3.0
    ingest_max_retries: int = 3

    graph_default_depth: int = 1
    graph_max_depth: int = 3
    graph_default_limit: int = 50
    graph_max_limit: int = 200

    model_config = {"env_prefix": "BIOMED_", "env_file": ".env"}


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    postgres_dsn: str = ""

    redis_url: str = "redis://localhost:6379/0"

    ncbi_api_key: str = ""

    ingest_rate_limit: float = 3.0
    ingest_max_retries: int = 3

    graph_default_depth: int = 3
    graph_max_depth: int = 5
    graph_default_limit: int = 200
    graph_max_limit: int = 1000

    rate_limit_graph_expand: str = "30/minute"
    rate_limit_graph_path: str = "10/minute"
    rate_limit_graph_network: str = "20/minute"
    rate_limit_search: str = "60/minute"

    model_config = {"env_prefix": "BIOMED_", "env_file": ".env"}


settings = Settings()


def validate_config_on_startup():
    """Reject known-default or empty credentials at startup.
    In production, consider logging warnings instead of crashing to avoid
    taking down the process for non-critical config issues.
    """
    if not settings.neo4j_password:
        raise RuntimeError("BIOMED_NEO4J_PASSWORD is required. Set it in .env")
    if not settings.postgres_dsn:
        raise RuntimeError("BIOMED_POSTGRES_DSN is required. Set it in .env")

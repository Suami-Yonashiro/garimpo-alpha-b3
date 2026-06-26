"""Configuracao central do projeto.

Le as credenciais do arquivo .env (local, fora do Git) de forma tipada e segura.
Em vez de espalhar os.getenv() pelo codigo, todo o projeto importa daqui:

    from src.config import settings
    engine = create_engine(settings.supabase_db_url)

Se uma variavel obrigatoria faltar, o erro aparece de forma clara e cedo.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # le do .env na raiz do projeto; ignora variaveis extras sem reclamar.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Conexao Postgres (Supabase). Default vazio para nao quebrar import sem .env;
    # quem for usar o banco valida a presenca antes de conectar.
    supabase_db_url: str = ""

    # REST API (uso futuro)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    def require_db(self) -> str:
        """Retorna a URL do banco ou levanta erro claro se nao estiver configurada."""
        if not self.supabase_db_url:
            raise RuntimeError(
                "SUPABASE_DB_URL nao configurada. Copie .env.example para .env "
                "e preencha a connection string do Supabase."
            )
        return self.supabase_db_url


# instancia unica importada pelo resto do projeto
settings = Settings()

"""Teste de fumaca do esqueleto: a configuracao carrega e o pacote importa.

Confiabilidade comeca cedo: este teste garante que a base do projeto esta sa
(import funciona, config carrega) antes de qualquer logica de negocio existir.
"""
from src.config import settings


def test_settings_carrega():
    # Deve instanciar sem erro mesmo sem .env (campos tem default vazio).
    assert settings is not None
    assert hasattr(settings, "supabase_db_url")


def test_require_db_sem_credencial_da_erro_claro():
    # Sem credencial, o erro deve ser explicito (e nao um crash obscuro depois).
    import pytest

    from src.config import Settings

    s = Settings(supabase_db_url="")
    with pytest.raises(RuntimeError, match="SUPABASE_DB_URL"):
        s.require_db()

"""Acesso ao banco (Supabase/Postgres).

Centraliza a criacao do engine SQLAlchemy para o projeto inteiro usar:

    from src.db import get_engine
    engine = get_engine()
"""
from sqlalchemy import Engine, create_engine

from src.config import settings


def get_engine() -> Engine:
    """Cria o engine de conexao com o Postgres do Supabase.

    pool_pre_ping=True: testa a conexao antes de usar (evita erro quando o
    Supabase free 'dorme' por inatividade e reabre a conexao).
    """
    return create_engine(settings.require_db(), pool_pre_ping=True)

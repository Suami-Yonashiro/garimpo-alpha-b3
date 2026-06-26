"""Teste de conexao com o Postgres do Supabase.

Diagnostica a string de conexao (SEM expor a senha) e tenta conectar.
A senha NUNCA e impressa; mostramos so estrutura (host, porta, usuario, db).
"""
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from src.config import settings


def diagnostico(raw: str) -> None:
    print("--- diagnostico da string (senha mascarada) ---")
    # "esqueleto": cada letra/numero vira x; so a ESTRUTURA aparece (seguro)
    esqueleto = "".join(c if not c.isalnum() else "x" for c in raw)
    print("  estrutura (x=letra/num):", esqueleto)
    print("  comprimento           :", len(raw))
    print("  comeca com postgresql://:", raw.startswith("postgresql://"))
    print("  contem espacos        :", " " in raw.strip(), "(espacos no meio sao problema)")
    print("  nº de '@'             :", raw.count("@"), "(deve ser 1)")
    url = make_url(raw)
    # mascara o usuario (contem o ref do projeto): mostra so o formato
    user = url.username or ""
    user_mask = (user.split(".")[0] + ".****") if "." in user else user
    print("  driver                :", url.drivername)
    print("  usuario               :", user_mask, "(deve ser 'postgres.<ref-do-projeto>')")
    print("  senha presente        :", bool(url.password))
    print("  host                  :", url.host)
    print("  porta                 :", url.port)
    print("  database              :", url.database)
    print("-" * 48)


def main() -> None:
    raw = settings.require_db()
    diagnostico(raw)

    print("Tentando conectar...")
    engine = create_engine(raw, pool_pre_ping=True)
    with engine.connect() as conn:
        db = conn.execute(text("select current_database();")).scalar()
        agora = conn.execute(text("select now();")).scalar()
    print("\n[OK] Conexao bem-sucedida!")
    print("  banco atual  :", db)
    print("  hora servidor:", agora)


if __name__ == "__main__":
    main()

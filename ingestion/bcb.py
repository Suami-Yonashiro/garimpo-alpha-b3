"""Integracao com o BCB (Banco Central) via python-bcb / SGS.

Por enquanto: SELIC meta (serie 432), usada como taxa livre de risco no WACC do DCF.
"""

# fallback caso a API do BCB esteja indisponivel (valor conservador, documentado)
SELIC_FALLBACK = 0.105


def selic_atual(default: float = SELIC_FALLBACK) -> float:
    """Retorna a SELIC meta atual em decimal (ex.: 0.1425 = 14,25% a.a.).

    Usa a serie 432 do SGS. Se a API falhar (rede), retorna o default conservador.
    """
    try:
        from bcb import sgs

        df = sgs.get({"selic": 432}, last=1)
        return float(df["selic"].iloc[-1]) / 100.0
    except Exception as exc:  # rede/indisponibilidade
        print(f"[aviso] SELIC do BCB indisponivel ({exc}); usando default {default:.1%}")
        return default

"""Integracao com o BCB (Banco Central) via python-bcb / SGS.

- SELIC meta (serie 432): taxa livre de risco no WACC do DCF.
- Series macro mensais (SELIC, IPCA 12m, cambio) como features do ML.
"""
import pandas as pd

# fallback caso a API do BCB esteja indisponivel (valor conservador, documentado)
SELIC_FALLBACK = 0.105

# codigos SGS das series macro usadas como features (PRD secao 4)
SGS_SELIC = 432       # Meta Selic (% a.a.)
SGS_IPCA_12M = 13522  # IPCA acumulado em 12 meses (%)
SGS_CAMBIO = 1        # Dolar (venda)


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


def series_macro(inicio: str = "2012-01-01") -> pd.DataFrame:
    """Series macro mensais (fim de mes): selic, ipca12, cambio. Para features do ML."""
    from bcb import sgs

    def _serie(codigo: int, nome: str) -> pd.Series:
        # SGS limita series diarias a janelas de 10 anos -> busca em blocos de 9 anos
        partes, atual, fim = [], pd.Timestamp(inicio), pd.Timestamp.today()
        while atual < fim:
            ate = min(atual + pd.DateOffset(years=9), fim)
            partes.append(
                sgs.get({"v": codigo}, start=atual.strftime("%Y-%m-%d"),
                        end=ate.strftime("%Y-%m-%d"))["v"]
            )
            atual = ate + pd.Timedelta(days=1)
        s = pd.concat(partes)
        s = s[~s.index.duplicated(keep="last")].rename(nome)  # evita indices duplicados
        return s

    macro = pd.concat(
        [_serie(SGS_SELIC, "selic"), _serie(SGS_IPCA_12M, "ipca12"),
         _serie(SGS_CAMBIO, "cambio")],
        axis=1,
    )
    # alinha tudo em fim de mes; ffill para preencher dias sem cotacao
    return macro.resample("ME").last().ffill()

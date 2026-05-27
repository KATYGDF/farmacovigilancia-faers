"""Detecção de sinais por disproporcionalidade em FAERS.

Implementa as três métricas mais usadas em farmacovigilância:
- **PRR** (Proportional Reporting Ratio) — Evans et al. 2001
- **ROR** (Reporting Odds Ratio) — Rothman et al. 2004
- **IC**  (Information Component, BCPNN) — Bate et al. 1998

Notação clássica da tabela 2×2 para um par (droga D, reação R):

                    Reação R    Outra reação
    Droga D           a            b
    Outra droga       c            d

PRR = (a / (a+b)) / (c / (c+d))
ROR = (a * d) / (b * c)
IC  = log2(a * (a+b+c+d) / ((a+b) * (a+c)))   # versão simplificada
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def build_2x2(
    df: pd.DataFrame,
    drug_col: str = "drug",
    reac_col: str = "reaction",
    min_reports: int = 3,
) -> pd.DataFrame:
    """Constrói tabela 2x2 (a, b, c, d) para cada par droga–reação.

    Args:
        df: DataFrame com uma linha por par (caso, droga, reação) deduplicado.
            Deve conter ao menos as colunas `drug_col` e `reac_col`.
        drug_col, reac_col: nomes das colunas.
        min_reports: descarta pares com a < min_reports (FDA usa 3 como padrão).

    Returns:
        DataFrame com colunas: drug, reaction, a, b, c, d, n
    """
    if drug_col not in df.columns or reac_col not in df.columns:
        raise ValueError(f"Colunas {drug_col!r} e {reac_col!r} obrigatórias.")

    pairs = (
        df.groupby([drug_col, reac_col]).size().rename("a").reset_index()
        .query("a >= @min_reports")
    )
    drug_totals = df.groupby(drug_col).size().rename("drug_total")
    reac_totals = df.groupby(reac_col).size().rename("reac_total")
    n_total = len(df)

    out = pairs.merge(drug_totals, left_on=drug_col, right_index=True)
    out = out.merge(reac_totals, left_on=reac_col, right_index=True)

    # a = par (droga, reação)
    # b = droga sem essa reação
    # c = essa reação com outras drogas
    # d = nem a droga nem a reação
    out["b"] = out["drug_total"] - out["a"]
    out["c"] = out["reac_total"] - out["a"]
    out["d"] = n_total - out["a"] - out["b"] - out["c"]
    out["n"] = n_total
    return out.drop(columns=["drug_total", "reac_total"]).rename(
        columns={drug_col: "drug", reac_col: "reaction"}
    )


def prr(contingency: pd.DataFrame) -> pd.DataFrame:
    """Calcula PRR + IC95% + chi-quadrado para cada par.

    Sinal positivo (FDA): PRR >= 2 AND chi2 >= 4 AND a >= 3.
    """
    a, b, c, d = contingency["a"], contingency["b"], contingency["c"], contingency["d"]

    p_drug = a / (a + b)
    p_other = c / (c + d).replace(0, np.nan)
    prr_val = p_drug / p_other

    # IC 95% no log do PRR (aproximação de Gaussian)
    log_prr = np.log(prr_val.replace(0, np.nan))
    se = np.sqrt(1 / a - 1 / (a + b) + 1 / c - 1 / (c + d))
    ci_low = np.exp(log_prr - 1.96 * se)
    ci_high = np.exp(log_prr + 1.96 * se)

    # Chi-quadrado de Yates
    n = a + b + c + d
    expected_a = (a + b) * (a + c) / n
    expected_b = (a + b) * (c + d) / n
    expected_c = (c + d) * (a + c) / n
    expected_d = (c + d) * (b + d) / n

    chi2 = (
        (np.abs(a - expected_a) - 0.5) ** 2 / expected_a
        + (np.abs(b - expected_b) - 0.5) ** 2 / expected_b
        + (np.abs(c - expected_c) - 0.5) ** 2 / expected_c
        + (np.abs(d - expected_d) - 0.5) ** 2 / expected_d
    )

    return contingency.assign(
        prr=prr_val,
        prr_ci_low=ci_low,
        prr_ci_high=ci_high,
        chi2=chi2,
        prr_signal=(prr_val >= 2) & (chi2 >= 4) & (a >= 3),
    )


def ror(contingency: pd.DataFrame) -> pd.DataFrame:
    """Calcula ROR + IC95%.

    Sinal positivo (EMA): IC95% inferior > 1 AND a >= 3.
    """
    a, b, c, d = contingency["a"], contingency["b"], contingency["c"], contingency["d"]
    ror_val = (a * d) / (b * c).replace(0, np.nan)

    log_ror = np.log(ror_val.replace(0, np.nan))
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    ci_low = np.exp(log_ror - 1.96 * se)
    ci_high = np.exp(log_ror + 1.96 * se)

    return contingency.assign(
        ror=ror_val,
        ror_ci_low=ci_low,
        ror_ci_high=ci_high,
        ror_signal=(ci_low > 1) & (a >= 3),
    )


def ic(contingency: pd.DataFrame) -> pd.DataFrame:
    """Calcula Information Component (BCPNN simplificado) + IC95%.

    IC = log2(p(D, R) / (p(D) * p(R))). Mede a força da associação.
    Sinal positivo (UMC): IC025 > 0.
    """
    a, b, c, d = contingency["a"], contingency["b"], contingency["c"], contingency["d"]
    n = a + b + c + d

    # Versão com smoothing (Norén et al. 2013)
    expected = (a + b) * (a + c) / n
    ic_val = np.log2((a + 0.5) / (expected + 0.5))

    # Aproximação do IC 95% (Bate 1998)
    var = (1 / (a + 0.5)) + (1 / (expected + 0.5))
    se = np.sqrt(var) / np.log(2)
    ci_low = ic_val - 1.96 * se
    ci_high = ic_val + 1.96 * se

    return contingency.assign(
        ic=ic_val,
        ic_ci_low=ci_low,
        ic_ci_high=ci_high,
        ic_signal=(ci_low > 0) & (a >= 3),
    )


def compute_all(
    df: pd.DataFrame,
    drug_col: str = "drug",
    reac_col: str = "reaction",
    min_reports: int = 3,
) -> pd.DataFrame:
    """Pipeline completo: monta 2x2 e calcula PRR + ROR + IC.

    Returns:
        DataFrame com todas as métricas por par droga-reação.
    """
    cont = build_2x2(df, drug_col=drug_col, reac_col=reac_col, min_reports=min_reports)
    cont = prr(cont)
    cont = ror(cont)
    cont = ic(cont)
    cont["any_signal"] = cont["prr_signal"] | cont["ror_signal"] | cont["ic_signal"]
    return cont

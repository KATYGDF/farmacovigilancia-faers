"""Feature engineering para o modelo de severidade.

Constrói uma tabela com **1 linha por caso** e features pré-desfecho.

Princípios:
- Não usar a coluna `reaction` como feature (vazamento: "DEATH" como reação implica morte)
- Usar apenas informação disponível no momento da reportagem inicial
- Lidar com alta cardinalidade do nome da droga (3.065 únicas pós-norm) via top-N
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

TOP_N_DRUGS_DEFAULT = 200
TOP_N_INDICATIONS_DEFAULT = 100


def _top_n_or_other(s: pd.Series, n: int, other: str = "OTHER") -> pd.Series:
    """Mantém top-N valores; resto vira `other`."""
    top = s.value_counts().head(n).index
    return s.where(s.isin(top), other)


def build_case_features(
    demo_norm: pd.DataFrame,
    drug_norm: pd.DataFrame,
    indi: pd.DataFrame | None,
    outc_agg: pd.DataFrame,
    rpsr: pd.DataFrame | None = None,
    top_n_drugs: int = TOP_N_DRUGS_DEFAULT,
    top_n_indications: int = TOP_N_INDICATIONS_DEFAULT,
) -> pd.DataFrame:
    """Constrói tabela de features por caso para predição de severidade.

    Args:
        demo_norm: DEMO dedup + age_years.
        drug_norm: DRUG com drug_norm (output de normalize_drug_table).
        indi: INDI (indicações) — opcional.
        outc_agg: saída de aggregate_outcomes (contém o target `serious`).
        rpsr: RPSR (tipo do reportante) — opcional.

    Returns:
        DataFrame com colunas:
            caseid, target,
            age_years, sex,
            n_drugs_total, n_drugs_ps, n_drugs_concomitant,
            n_indications,
            primary_drug, primary_indication, reporter_type
    """
    demo = demo_norm[["caseid", "age_years", "sex"]].copy()
    demo["caseid"] = demo["caseid"].astype(str)
    demo["sex"] = demo["sex"].fillna("UNK")

    drug = drug_norm[["caseid", "drug_norm", "role_cod"]].copy()
    drug["caseid"] = drug["caseid"].astype(str)
    drug["role_cod"] = drug["role_cod"].fillna("").str.upper()

    # Agregações no nível do caso
    n_drugs_total = drug.groupby("caseid").size().rename("n_drugs_total")
    n_drugs_ps = (drug["role_cod"] == "PS").groupby(drug["caseid"]).sum().rename("n_drugs_ps")
    n_drugs_conc = (drug["role_cod"] == "C").groupby(drug["caseid"]).sum().rename("n_drugs_concomitant")

    # Droga primária por caso (a primeira PS, ou primeira qualquer)
    drug["__ord"] = (drug["role_cod"] != "PS").astype(int)
    primary = drug.sort_values(["caseid", "__ord"]).drop_duplicates("caseid", keep="first")
    primary = primary.set_index("caseid")["drug_norm"].rename("primary_drug")

    feats = demo.set_index("caseid").join([n_drugs_total, n_drugs_ps, n_drugs_conc, primary])
    feats = feats.fillna({"n_drugs_total": 0, "n_drugs_ps": 0, "n_drugs_concomitant": 0})
    feats["primary_drug"] = feats["primary_drug"].fillna("UNKNOWN")

    # Indicação primária (do PS quando possível)
    if indi is not None:
        ind = indi[["caseid", "indi_pt"]].copy()
        ind["caseid"] = ind["caseid"].astype(str)
        ind["indi_pt"] = ind["indi_pt"].fillna("").str.upper().str.strip()
        ind = ind[ind["indi_pt"] != ""]
        n_ind = ind.groupby("caseid").size().rename("n_indications")
        primary_ind = ind.drop_duplicates("caseid", keep="first").set_index("caseid")["indi_pt"].rename("primary_indication")
        feats = feats.join([n_ind, primary_ind])
        feats["n_indications"] = feats["n_indications"].fillna(0)
        feats["primary_indication"] = feats["primary_indication"].fillna("UNKNOWN")
    else:
        feats["n_indications"] = 0
        feats["primary_indication"] = "UNKNOWN"

    # Tipo de reportante
    if rpsr is not None and "rpsr_cod" in rpsr.columns:
        r = rpsr[["caseid", "rpsr_cod"]].copy()
        r["caseid"] = r["caseid"].astype(str)
        r["rpsr_cod"] = r["rpsr_cod"].fillna("UNK")
        reporter = r.drop_duplicates("caseid", keep="first").set_index("caseid")["rpsr_cod"].rename("reporter_type")
        feats = feats.join(reporter)
        feats["reporter_type"] = feats["reporter_type"].fillna("UNK")
    else:
        feats["reporter_type"] = "UNK"

    # Limitar cardinalidade
    feats["primary_drug"] = _top_n_or_other(feats["primary_drug"], top_n_drugs)
    feats["primary_indication"] = _top_n_or_other(feats["primary_indication"], top_n_indications)

    # Target
    target = outc_agg[["caseid", "serious"]].copy()
    target["caseid"] = target["caseid"].astype(str)
    target = target.set_index("caseid")["serious"].astype(int).rename("target")

    feats = feats.join(target, how="inner")  # mantém só casos com desfecho conhecido
    feats = feats.reset_index()
    return feats


NUMERIC_COLS = ["age_years", "n_drugs_total", "n_drugs_ps", "n_drugs_concomitant", "n_indications"]
CATEGORICAL_COLS = ["sex", "primary_drug", "primary_indication", "reporter_type"]

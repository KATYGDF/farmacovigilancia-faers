"""Limpeza e normalização das tabelas do FAERS.

Principais desafios tratados:
1. **Deduplicação** — o mesmo caso pode aparecer em múltiplos trimestres com
   atualizações. Mantemos a versão mais recente por `caseid`.
2. **Normalização de nomes de medicamentos** — FAERS aceita texto livre, então
   "warfarin", "WARFARIN SODIUM", "Coumadin", "warfarin 5mg" etc. precisam ser
   normalizados.
3. **Codificação de desfechos** — combinamos os 7 códigos OUTC em um flag
   binário "serious" (DE/LT/HO/DS/CA/RI = sério; OT = outro).
4. **Idade e sexo** — converter de string + unidade para anos numéricos.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Deduplicação
# ---------------------------------------------------------------------------

def dedupe_demo(demo: pd.DataFrame) -> pd.DataFrame:
    """Mantém apenas a versão mais recente de cada caso.

    Usa `caseid` + `caseversion` para ordenar; pega a maior versão.
    """
    out = demo.copy()
    out["caseversion_num"] = pd.to_numeric(out["caseversion"], errors="coerce").fillna(0)
    out = out.sort_values(["caseid", "caseversion_num"]).drop_duplicates(
        "caseid", keep="last"
    )
    return out.drop(columns=["caseversion_num"])


# ---------------------------------------------------------------------------
# Normalização de idade
# ---------------------------------------------------------------------------

AGE_TO_YEARS = {
    "DEC": 10.0,    # décadas
    "YR": 1.0,      # anos
    "MON": 1 / 12,  # meses
    "WK": 1 / 52,   # semanas
    "DY": 1 / 365,  # dias
    "HR": 1 / 8760, # horas
}


def normalize_age(demo: pd.DataFrame) -> pd.DataFrame:
    """Converte (age, age_cod) -> age_years (float)."""
    out = demo.copy()
    age_num = pd.to_numeric(out.get("age"), errors="coerce")
    cod = out.get("age_cod", pd.Series(["YR"] * len(out)))
    factor = cod.map(AGE_TO_YEARS).fillna(1.0)
    out["age_years"] = age_num * factor
    # filtrar fora valores absurdos
    out.loc[(out["age_years"] < 0) | (out["age_years"] > 120), "age_years"] = np.nan
    return out


# ---------------------------------------------------------------------------
# Normalização de nomes de medicamentos
# ---------------------------------------------------------------------------

# Sufixos e padrões removidos em normalização
_REMOVE_PATTERNS = [
    r"\d+\s*(mg|mcg|g|ml|iu|units?|%)\b",   # 5mg, 100 mcg, 50%, 2 IU
    r"\b(sodium|hydrochloride|sulfate|tartrate|citrate|phosphate|maleate|succinate|fumarate|hcl)\b",  # sais
    r"\b(tablet|capsule|solution|injection|cream|gel|patch|oral|iv|im|sc|topical)\b",
    r"\bunknown\b",
    r"[\(\)\[\]/\\,]",
    r"\s+",  # múltiplos espaços
]
_REMOVE_RE = [re.compile(p, re.IGNORECASE) for p in _REMOVE_PATTERNS]


def normalize_drug_name(name: str | float) -> str:
    """Aplica regras heurísticas para normalizar texto de medicamento."""
    if pd.isna(name) or not isinstance(name, str):
        return ""
    s = name.upper().strip()
    for pat in _REMOVE_RE:
        s = pat.sub(" ", s)
    return " ".join(s.split())


def normalize_drug_table(drug: pd.DataFrame) -> pd.DataFrame:
    """Adiciona coluna `drug_norm` à tabela DRUG."""
    out = drug.copy()
    # Preferimos prod_ai (active ingredient) quando disponível, senão drugname
    primary = out.get("prod_ai", pd.Series([""] * len(out))).fillna("")
    fallback = out.get("drugname", pd.Series([""] * len(out))).fillna("")
    raw = primary.where(primary.str.len() > 0, fallback)
    out["drug_norm"] = raw.apply(normalize_drug_name)
    out = out[out["drug_norm"] != ""].copy()
    return out


# ---------------------------------------------------------------------------
# Desfechos
# ---------------------------------------------------------------------------

SERIOUS_OUTCOMES = {"DE", "LT", "HO", "DS", "CA", "RI"}
# DE: Death  LT: Life-Threatening  HO: Hospitalization  DS: Disability
# CA: Congenital Anomaly  RI: Required Intervention  OT: Other Serious


def aggregate_outcomes(outc: pd.DataFrame) -> pd.DataFrame:
    """Agrega múltiplos códigos OUTC por caso em um único registro.

    Returns:
        DataFrame com colunas: caseid, primaryid, outcomes (str), serious (bool),
        death (bool), hospitalization (bool).
    """
    out = outc.copy()
    out["caseid"] = out["caseid"].astype(str)
    grouped = (
        out.groupby(["caseid", "primaryid"])["outc_cod"]
        .apply(lambda s: sorted(set(s.dropna())))
        .reset_index()
    )
    grouped["outcomes"] = grouped["outc_cod"].apply(lambda lst: "|".join(lst))
    grouped["serious"] = grouped["outc_cod"].apply(
        lambda lst: any(c in SERIOUS_OUTCOMES for c in lst)
    )
    grouped["death"] = grouped["outc_cod"].apply(lambda lst: "DE" in lst)
    grouped["hospitalization"] = grouped["outc_cod"].apply(lambda lst: "HO" in lst)
    return grouped.drop(columns=["outc_cod"])


# ---------------------------------------------------------------------------
# Construção do dataset analítico (1 linha = par caso × droga × reação)
# ---------------------------------------------------------------------------

def build_long(
    demo: pd.DataFrame,
    drug: pd.DataFrame,
    reac: pd.DataFrame,
    outc: pd.DataFrame | None = None,
    only_primary_suspect: bool = True,
) -> pd.DataFrame:
    """Constrói tabela "long" para análise de sinais.

    Cada linha = (caso × droga × reação). Se `only_primary_suspect`, filtra
    apenas medicamentos com `role_cod == 'PS'`.

    Args:
        demo, drug, reac: tabelas já normalizadas (drug com `drug_norm`).
        outc: tabela de desfechos opcional (para adicionar flags serious/death/HO).
        only_primary_suspect: se True (padrão), filtra role_cod=PS.

    Returns:
        DataFrame com colunas: caseid, primaryid, drug, reaction, [outcomes...].
    """
    demo_dedup = dedupe_demo(demo)
    case_ids = set(demo_dedup["caseid"].astype(str))

    d = drug.copy()
    d["caseid"] = d["caseid"].astype(str)
    if only_primary_suspect and "role_cod" in d.columns:
        d = d[d["role_cod"].fillna("").str.upper() == "PS"]
    d = d[d["caseid"].isin(case_ids)]

    r = reac.copy()
    r["caseid"] = r["caseid"].astype(str)
    r = r[r["caseid"].isin(case_ids)]
    r["reaction"] = r["pt"].fillna("").str.upper().str.strip()
    r = r[r["reaction"] != ""]

    # Junta drug × reaction por caso (produto cartesiano DENTRO de cada caso)
    drug_slim = d[["caseid", "drug_norm"]].drop_duplicates().rename(columns={"drug_norm": "drug"})
    reac_slim = r[["caseid", "reaction"]].drop_duplicates()

    long = drug_slim.merge(reac_slim, on="caseid")

    # Adiciona demografia básica
    demo_slim = demo_dedup[["caseid", "primaryid", "age_years", "sex"]] if "age_years" in demo_dedup else \
                demo_dedup[["caseid", "primaryid"]]
    long = long.merge(demo_slim, on="caseid", how="left")

    # Adiciona desfechos se fornecidos
    if outc is not None:
        outc_agg = aggregate_outcomes(outc)
        long = long.merge(
            outc_agg[["caseid", "serious", "death", "hospitalization", "outcomes"]],
            on="caseid", how="left",
        )
        long[["serious", "death", "hospitalization"]] = long[
            ["serious", "death", "hospitalization"]
        ].fillna(False)

    return long

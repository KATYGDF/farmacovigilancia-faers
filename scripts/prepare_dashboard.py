"""Pré-computa resumos leves para o dashboard Streamlit.

Gera arquivos pequenos que podem ser carregados rapidamente no Streamlit Cloud,
sem necessidade de processar os parquets grandes (drug.parquet de 121 MB etc.).

Saídas em data/processed/dashboard/:
- summary.json           — KPIs globais
- top_drugs.parquet      — top 200 drogas com freq + classe predominante
- top_reactions.parquet  — top 200 reações
- outcomes.parquet       — distribuição de OUTC
- drug_list.json         — lista de drogas usadas pelo modelo (para dropdown)
- indication_list.json   — lista de indicações usadas pelo modelo
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import pandas as pd

from src.preprocess import (
    dedupe_demo, normalize_age, normalize_drug_table, aggregate_outcomes,
)

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
DASH = PROCESSED / "dashboard"
DASH.mkdir(parents=True, exist_ok=True)


def main():
    print("Carregando dados brutos...")
    demo = normalize_age(dedupe_demo(pd.read_parquet(PROCESSED / "demo_2023.parquet")))
    drug = normalize_drug_table(pd.read_parquet(PROCESSED / "drug_2023.parquet"))
    reac = pd.read_parquet(PROCESSED / "reac_2023.parquet")
    outc = pd.read_parquet(PROCESSED / "outc_2023.parquet")
    outc_agg = aggregate_outcomes(outc)

    # 1. Summary global
    print("Calculando KPIs...")
    serious_rate = outc_agg["serious"].mean()
    death_rate = outc_agg["death"].mean()
    summary = {
        "total_cases": int(len(demo)),
        "total_drug_reports": int(len(drug)),
        "total_unique_drugs": int(drug["drug_norm"].nunique()),
        "total_reactions": int(reac["pt"].notna().sum()),
        "total_unique_reactions": int(reac["pt"].nunique()),
        "cases_with_outcome": int(len(outc_agg)),
        "serious_rate_pct": round(float(serious_rate) * 100, 2),
        "death_rate_pct": round(float(death_rate) * 100, 2),
        "year": 2023,
        "n_quarters": 4,
    }
    (DASH / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"  [ok]summary.json: {summary}")

    # 2. Top drogas PS
    print("Top drogas (PS)...")
    ps = drug[drug["role_cod"].fillna("").str.upper() == "PS"]
    top_drugs = ps["drug_norm"].value_counts().head(200).reset_index()
    top_drugs.columns = ["drug", "count"]
    top_drugs.to_parquet(DASH / "top_drugs.parquet", index=False)
    print(f"  [ok]top_drugs.parquet: {len(top_drugs)} drogas")

    # 3. Top reações
    print("Top reações...")
    reac_clean = reac.copy()
    reac_clean["pt"] = reac_clean["pt"].fillna("").str.upper().str.strip()
    top_reac = reac_clean[reac_clean["pt"] != ""]["pt"].value_counts().head(200).reset_index()
    top_reac.columns = ["reaction", "count"]
    top_reac.to_parquet(DASH / "top_reactions.parquet", index=False)
    print(f"  [ok]top_reactions.parquet: {len(top_reac)} reações")

    # 4. Distribuição de OUTC
    OUTC_LABELS = {
        "DE": "Morte",
        "LT": "Risco de vida",
        "HO": "Hospitalização",
        "DS": "Incapacidade",
        "CA": "Anomalia congênita",
        "RI": "Intervenção necessária",
        "OT": "Outro sério",
    }
    outc_counts = outc["outc_cod"].value_counts().reset_index()
    outc_counts.columns = ["code", "count"]
    outc_counts["label"] = outc_counts["code"].map(OUTC_LABELS).fillna(outc_counts["code"])
    outc_counts.to_parquet(DASH / "outcomes.parquet", index=False)
    print(f"  [ok]outcomes.parquet: {len(outc_counts)} categorias")

    # 5. Listas para dropdowns do modelo
    print("Extraindo listas do preprocessor de severidade...")
    pre = joblib.load(ROOT / "models" / "preprocessor_severity.pkl")
    cat_transformer = pre.named_transformers_["cat"].named_steps["ohe"]
    cat_cols = ["sex", "primary_drug", "primary_indication", "reporter_type"]
    drug_idx = cat_cols.index("primary_drug")
    ind_idx = cat_cols.index("primary_indication")
    sex_idx = cat_cols.index("sex")
    reporter_idx = cat_cols.index("reporter_type")

    cats = cat_transformer.categories_
    lists = {
        "sex": [str(x) for x in cats[sex_idx] if str(x) != "infrequent_sklearn"],
        "primary_drug": sorted([str(x) for x in cats[drug_idx] if str(x) != "infrequent_sklearn"]),
        "primary_indication": sorted([str(x) for x in cats[ind_idx] if str(x) != "infrequent_sklearn"]),
        "reporter_type": [str(x) for x in cats[reporter_idx] if str(x) != "infrequent_sklearn"],
    }
    (DASH / "model_lists.json").write_text(json.dumps(lists, indent=2))
    print(f"  [ok]model_lists.json: drogas={len(lists['primary_drug'])}, indicações={len(lists['primary_indication'])}")

    print("\n[OK] Tudo pronto em data/processed/dashboard/")
    for f in sorted(DASH.iterdir()):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:30s}  {size_kb:8.1f} KB")


if __name__ == "__main__":
    main()

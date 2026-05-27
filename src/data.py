"""Download e parsing dos arquivos trimestrais do FAERS (FDA AERS).

Estrutura de cada ZIP trimestral:
    faers_ascii_YYYYqN.zip
    └── ASCII/
        ├── DEMOyyqN.txt   demografia + identificação do caso
        ├── DRUGyyqN.txt   medicamentos
        ├── REACyyqN.txt   reações (MedDRA preferred term)
        ├── OUTCyyqN.txt   desfechos (DE, LT, HO, DS, CA, RI, OT)
        ├── INDIyyqN.txt   indicações de uso
        ├── RPSRyyqN.txt   tipo de reportante
        └── THERyyqN.txt   datas de terapia

Arquivos são texto delimitado por `$`, encoding "latin-1".
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

FAERS_BASE_URL = "https://fis.fda.gov/content/Exports"

TABLES = ["DEMO", "DRUG", "REAC", "OUTC", "INDI", "RPSR", "THER"]


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def _zip_url(year: int, quarter: int) -> str:
    """URL do ZIP trimestral. FDA usa minúscula 'q'."""
    return f"{FAERS_BASE_URL}/faers_ascii_{year}q{quarter}.zip"


def _local_zip(year: int, quarter: int) -> Path:
    return RAW_DIR / f"faers_ascii_{year}q{quarter}.zip"


def download_quarter(year: int, quarter: int, verify_ssl: bool = True) -> Path:
    """Baixa um trimestre do FAERS para data/raw/."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = _local_zip(year, quarter)
    if out.exists():
        print(f"[skip] {out.name} já existe ({out.stat().st_size / 1e6:.1f} MB)")
        return out

    url = _zip_url(year, quarter)
    print(f"Baixando {url} ...")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=300, verify=verify_ssl, stream=True)
        resp.raise_for_status()
    except requests.exceptions.SSLError:
        print("[aviso] Falha SSL — tentando novamente sem verificação.")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resp = requests.get(url, headers=headers, timeout=300, verify=False, stream=True)
        resp.raise_for_status()

    total = int(resp.headers.get("Content-Length", 0))
    written = 0
    with open(out, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
                written += len(chunk)
                if total:
                    pct = 100 * written / total
                    print(f"  {written / 1e6:.0f} / {total / 1e6:.0f} MB ({pct:.0f}%)", end="\r")
    print(f"\n[ok] {out.name} ({written / 1e6:.1f} MB)")
    return out


def download_year(year: int, quarters: Iterable[int] = (1, 2, 3, 4)) -> list[Path]:
    """Baixa todos os trimestres do ano."""
    return [download_quarter(year, q) for q in quarters]


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _ascii_filename(table: str, year: int, quarter: int) -> str:
    """Nome do arquivo dentro do ZIP. Ex: DEMO23Q1.txt"""
    yy = f"{year % 100:02d}"
    return f"{table}{yy}Q{quarter}.txt"


def read_table(year: int, quarter: int, table: str) -> pd.DataFrame:
    """Lê uma tabela específica de um trimestre.

    Retorna DataFrame; FAERS usa '$' como delimitador e latin-1 como encoding.
    """
    table = table.upper()
    if table not in TABLES:
        raise ValueError(f"Tabela {table!r} desconhecida. Use uma de {TABLES}.")

    zip_path = _local_zip(year, quarter)
    if not zip_path.exists():
        download_quarter(year, quarter)

    fname = _ascii_filename(table, year, quarter)
    with zipfile.ZipFile(zip_path) as zf:
        # Procura por correspondência case-insensitive (ASCII/ ou ascii/)
        candidates = [n for n in zf.namelist() if n.upper().endswith(fname.upper())]
        if not candidates:
            raise FileNotFoundError(f"{fname} não encontrado em {zip_path.name}")
        with zf.open(candidates[0]) as fp:
            df = pd.read_csv(
                fp,
                sep="$",
                encoding="latin-1",
                dtype=str,
                on_bad_lines="warn",
                low_memory=False,
            )
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def load_year(year: int, table: str, quarters: Iterable[int] = (1, 2, 3, 4)) -> pd.DataFrame:
    """Concatena uma tabela de todos os trimestres do ano informado."""
    frames = []
    for q in quarters:
        df = read_table(year, q, table)
        df["quarter"] = q
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    print(f"[{table}] {len(out):,} linhas em {year}")
    return out


def cache_year_parquet(year: int, table: str, quarters: Iterable[int] = (1, 2, 3, 4)) -> Path:
    """Lê todos os trimestres do ano e salva como parquet em data/processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / f"{table.lower()}_{year}.parquet"
    if out.exists():
        print(f"[skip] {out.name} já existe")
        return out
    df = load_year(year, table, quarters)
    df.to_parquet(out, index=False)
    print(f"[ok] {out.name} ({out.stat().st_size / 1e6:.1f} MB)")
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    YEAR = 2023
    download_year(YEAR)
    print("\n=== Convertendo para parquet ===")
    for tbl in TABLES:
        cache_year_parquet(YEAR, tbl)

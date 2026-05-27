"""Análise de rede droga-droga sobre o FAERS.

- Nós: medicamentos (limitados aos top-N por frequência para tractabilidade)
- Arestas: co-reporte no mesmo caso (qualquer role)
- Pesos: número de casos em que ambas as drogas aparecem
"""
from __future__ import annotations

from itertools import combinations
from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd


def top_drugs(drug_norm: pd.DataFrame, n: int = 200) -> list[str]:
    """Retorna lista das N drogas mais reportadas (qualquer role)."""
    return drug_norm["drug_norm"].value_counts().head(n).index.tolist()


def build_cooccurrence(
    drug_norm: pd.DataFrame,
    drugs_keep: Iterable[str],
    min_coreport: int = 50,
) -> pd.DataFrame:
    """Constrói tabela de co-ocorrência (droga A, droga B, casos juntos).

    Args:
        drug_norm: tabela DRUG normalizada (com coluna `drug_norm`).
        drugs_keep: drogas a considerar (limita o grafo).
        min_coreport: descarta pares com menos de N co-reportes.

    Returns:
        DataFrame com colunas: source, target, weight.
    """
    keep = set(drugs_keep)
    d = drug_norm[drug_norm["drug_norm"].isin(keep)].copy()
    d["caseid"] = d["caseid"].astype(str)

    # Set de drogas por caso (deduplica)
    by_case = d.groupby("caseid")["drug_norm"].agg(lambda s: tuple(sorted(set(s))))
    # Só nos interessam casos com 2+ drogas
    by_case = by_case[by_case.apply(len) >= 2]

    # Gerar pares e contar
    pair_counts: dict[tuple[str, str], int] = {}
    for drugs in by_case.values:
        for a, b in combinations(drugs, 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    edges = pd.DataFrame(
        [(a, b, w) for (a, b), w in pair_counts.items() if w >= min_coreport],
        columns=["source", "target", "weight"],
    )
    return edges.sort_values("weight", ascending=False).reset_index(drop=True)


def build_graph(edges: pd.DataFrame) -> nx.Graph:
    """Constrói grafo NetworkX a partir de tabela de arestas."""
    g = nx.from_pandas_edgelist(edges, "source", "target", edge_attr="weight")
    return g


def centrality_metrics(g: nx.Graph) -> pd.DataFrame:
    """Calcula centralidade de grau, eigenvector, betweenness e clustering."""
    degree = dict(g.degree(weight="weight"))
    try:
        eigen = nx.eigenvector_centrality_numpy(g, weight="weight")
    except Exception:
        eigen = nx.eigenvector_centrality(g, weight="weight", max_iter=1000)
    between = nx.betweenness_centrality(g, weight="weight", k=min(500, len(g)))
    clustering = nx.clustering(g, weight="weight")

    out = pd.DataFrame({
        "drug": list(g.nodes),
        "degree_w": [degree[n] for n in g.nodes],
        "eigenvector": [eigen[n] for n in g.nodes],
        "betweenness": [between[n] for n in g.nodes],
        "clustering": [clustering[n] for n in g.nodes],
    }).sort_values("eigenvector", ascending=False).reset_index(drop=True)
    return out


def detect_communities(g: nx.Graph, seed: int = 42) -> dict[str, int]:
    """Detecta comunidades com Louvain. Retorna dict nó -> id da comunidade."""
    try:
        import community as community_louvain
        return community_louvain.best_partition(g, weight="weight", random_state=seed)
    except ImportError:
        # Fallback para greedy modularity
        comms = nx.algorithms.community.greedy_modularity_communities(g, weight="weight")
        return {node: cid for cid, comm in enumerate(comms) for node in comm}

"""
civic_framework/metrics.py

Métricas cívicas para análise de atividade legislativa municipal.

Metodologia documentada publicamente (princípio de transparência algorítmica):
- IAL: Índice de Atividade Legislativa — modelo ponderado, não oráculo
- Z-Score: desvio estatístico por vereador ao longo do tempo
- ICG: Índice de Concentração Geográfica (Herfindahl) por bairro

IMPORTANTE: Todos os pesos são parâmetros, não verdades absolutas.
Documente e versione qualquer mudança metodológica.
"""

import math
import logging
from typing import Dict, List, Any, Tuple

import pandas as pd
import numpy as np

log = logging.getLogger(__name__)


# ── Pesos do IAL (documentar qualquer alteração) ──────────────────
# v1.0 — pesos igualitários como baseline neutro
IAL_PESOS = {
    "proposicoes": 0.50,    # Produção legislativa (principal)
    "participacao": 0.30,   # Presença em pautas/sessões
    "relatorias": 0.20,     # Relatorias e autorias de destaque
}
IAL_VERSION = "1.0"


def calcular_ial(
    df_vereadores: pd.DataFrame,
    df_proposicoes: pd.DataFrame,
    df_pautas: pd.DataFrame,
    pesos: Dict[str, float] = None,
) -> pd.DataFrame:
    """
    Calcula o Índice de Atividade Legislativa (IAL) por vereador.

    IAL = (n_proposicoes * w1) + (participacao_pautas * w2) + (relatorias * w3)
    Normalizado para [0, 100].

    Retorna DataFrame com colunas: uid, nome, n_proposicoes, participacao,
    relatorias, ial_bruto, ial_norm, percentil.
    """
    if pesos is None:
        pesos = IAL_PESOS

    # Garante que os pesos somam 1.0
    total_pesos = sum(pesos.values())
    pesos = {k: v / total_pesos for k, v in pesos.items()}

    resultados = []

    for _, ver in df_vereadores.iterrows():
        nome = ver.get("nome", "N/A")
        uid = ver.get("uid", ver.get("id", nome))

        # Proposições do vereador (por nome ou uid)
        mask_prop = df_proposicoes.get("autor", pd.Series(dtype=str)).str.contains(
            nome, case=False, na=False
        ) if not df_proposicoes.empty else pd.Series([], dtype=bool)
        n_prop = int(mask_prop.sum()) if len(mask_prop) > 0 else 0

        # Participação em pautas (proxy: pautas no período)
        # Sem dados de presença individuais, usa o total de pautas como baseline
        n_pautas = len(df_pautas) if not df_pautas.empty else 0
        participacao = min(n_pautas / max(len(df_pautas), 1), 1.0) if n_pautas > 0 else 0

        # Relatorias: assumimos 0 quando dado não disponível (dados CMF não incluem)
        relatorias = 0

        ial_bruto = (
            n_prop * pesos["proposicoes"] +
            participacao * pesos["participacao"] * 10 +  # escala para comparar com prop
            relatorias * pesos["relatorias"]
        )

        resultados.append({
            "uid": uid,
            "nome": nome,
            "partido": ver.get("partido", "N/A"),
            "n_proposicoes": n_prop,
            "participacao_pautas": round(participacao * 100, 1),
            "relatorias": relatorias,
            "ial_bruto": round(ial_bruto, 3),
        })

    df_ial = pd.DataFrame(resultados)
    if df_ial.empty:
        return df_ial

    # Normalização Min-Max para [0, 100]
    ial_min = df_ial["ial_bruto"].min()
    ial_max = df_ial["ial_bruto"].max()
    epsilon = 1e-9
    df_ial["ial_norm"] = (
        (df_ial["ial_bruto"] - ial_min) / (ial_max - ial_min + epsilon) * 100
    ).round(1)

    # Percentil para contexto relativo
    df_ial["percentil"] = df_ial["ial_norm"].rank(pct=True).mul(100).round(0).astype(int)

    # Metadados metodológicos
    df_ial["metodologia_versao"] = IAL_VERSION
    df_ial["pesos_json"] = str(pesos)

    return df_ial.sort_values("ial_norm", ascending=False).reset_index(drop=True)


def detectar_anomalias_vereador(
    df_historico: pd.DataFrame,
    coluna_valor: str = "n_proposicoes",
    threshold: float = 2.0,
) -> pd.DataFrame:
    """
    Detecta anomalias estatísticas na atividade de vereadores ao longo do tempo.

    Usa Z-Score por vereador (variação em relação à sua própria média histórica).
    threshold=2.0 → alerta; 3.0 → anomalia forte.

    df_historico deve conter: uid, nome, periodo (YYYYMM), <coluna_valor>
    """
    if df_historico.empty or coluna_valor not in df_historico.columns:
        return pd.DataFrame()

    anomalias = []
    for uid, grupo in df_historico.groupby("uid"):
        if len(grupo) < 3:
            continue
        media = grupo[coluna_valor].mean()
        std = grupo[coluna_valor].std()
        if std == 0:
            continue
        grupo = grupo.copy()
        grupo["z_score"] = (grupo[coluna_valor] - media) / std
        grupo["is_anomalia"] = grupo["z_score"].abs() > threshold
        anomalias.append(grupo[grupo["is_anomalia"]])

    return pd.concat(anomalias) if anomalias else pd.DataFrame()


def concentracao_geografica(df_proposicoes: pd.DataFrame, coluna_bairro: str = "bairro") -> pd.DataFrame:
    """
    Calcula o Índice de Concentração Geográfica (ICG) por bairro.

    Baseado no Índice Herfindahl-Hirschman (HHI):
    ICG = Σ (share_i)²  → varia de 0 (disperso) a 1 (concentrado num bairro)

    Retorna ranking de bairros e o ICG global.
    """
    if df_proposicoes.empty or coluna_bairro not in df_proposicoes.columns:
        return pd.DataFrame()

    contagem = df_proposicoes[coluna_bairro].value_counts()
    total = contagem.sum()
    shares = contagem / total
    hhi = (shares ** 2).sum()

    df_bairros = pd.DataFrame({
        "bairro": contagem.index,
        "n_proposicoes": contagem.values,
        "share_pct": (shares * 100).round(1).values,
    })
    df_bairros["icg_global"] = round(hhi, 4)
    df_bairros["interpretacao"] = (
        "Alta concentração" if hhi > 0.25
        else "Moderada" if hhi > 0.10
        else "Bem distribuído"
    )

    return df_bairros.reset_index(drop=True)


def gerar_relatorio_resumo(cidade_id: str, df_ial: pd.DataFrame, df_anomalias: pd.DataFrame) -> str:
    """
    Gera um relatório textual em Markdown da situação legislativa atual.
    Projetado para ser base de relatórios semanais automatizados.
    """
    if df_ial.empty:
        return f"# Relatório {cidade_id}\n\n⚠️ Dados insuficientes para análise."

    top3 = df_ial.head(3)[["nome", "ial_norm", "n_proposicoes"]].to_string(index=False)
    n_anomalias = len(df_anomalias) if not df_anomalias.empty else 0

    return f"""# 📊 Relatório Legislativo — {cidade_id.title()}

**Metodologia IAL v{IAL_VERSION}** | Pesos: {IAL_PESOS}

## 🏆 Top 3 Mais Ativos (IAL)
```
{top3}
```

## 🚨 Anomalias Detectadas
- **{n_anomalias}** variações incomuns identificadas (Z-Score > 2σ)

> ⚠️ IAL é uma ferramenta analítica, não um julgamento de valor.
> A metodologia completa está documentada no repositório.
"""

"""
Módulo de inteligência e auditoria de gastos.
Implementa detecção de anomalias, verificação de limites e análise estatística.
"""

import pandas as pd
import numpy as np

# Limites aproximados da Cota para o Exercício da Atividade Parlamentar (CEAP) por UF (2024)
# Fonte: Ato da Mesa n. 43/2009 e atualizações.
LIMITES_CEAP = {
    "AC": 50403.49, "AL": 46423.57, "AM": 49434.61, "AP": 48934.33,
    "BA": 43906.13, "CE": 47214.28, "DF": 35246.33, "ES": 42167.36,
    "GO": 40166.42, "MA": 46977.40, "MG": 40489.15, "MS": 45041.69,
    "MT": 44101.99, "PA": 46995.96, "PB": 46777.62, "PE": 46395.02,
    "PI": 45663.15, "PR": 43336.87, "RJ": 40320.18, "RN": 47525.86,
    "RO": 48332.61, "RR": 51433.00, "RS": 45318.42, "SC": 44031.11,
    "SE": 45097.35, "SP": 41530.40, "TO": 44129.58
}

def detect_outliers(df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
    """
    Identifica gastos anômalos usando Z-Score dentro de cada categoria.
    
    Args:
        df: DataFrame de despesas.
        threshold: Limite de desvios padrão para considerar um outlier (default 3.0).
        
    Returns:
        DataFrame contendo apenas as despesas consideradas anômalas.
    """
    if df.empty or "valor_liquido" not in df.columns or "categoria" not in df.columns:
        return pd.DataFrame()

    outliers_list = []
    
    for categoria, group in df.groupby("categoria"):
        if len(group) < 3:  # Amostra muito pequena para estatística
            continue
            
        mean = group["valor_liquido"].mean()
        std = group["valor_liquido"].std()
        
        if std == 0:
            continue
            
        z_scores = (group["valor_liquido"] - mean) / std
        outliers = group[np.abs(z_scores) > threshold].copy()
        
        if not outliers.empty:
            outliers["z_score"] = z_scores[np.abs(z_scores) > threshold]
            outliers["media_categoria"] = mean
            outliers_list.append(outliers)
            
    return pd.concat(outliers_list) if outliers_list else pd.DataFrame()

def check_ceap_usage(df: pd.DataFrame, uf: str) -> dict:
    """
    Verifica o uso da cota mensal em relação ao limite da UF.
    
    Returns:
        Dicionário com percentual de uso e se excedeu.
    """
    limite = LIMITES_CEAP.get(uf.upper(), 40000.0)  # Fallback generoso
    
    if df.empty or "valor_liquido" not in df.columns:
        return {"total": 0, "limite": limite, "percentual": 0, "excedeu": False}

    # Agrupar por ano/mês para ver o gasto total mensal
    resumo_mensal = df.groupby(["ano", "mes"])["valor_liquido"].sum().reset_index()
    
    if resumo_mensal.empty:
        return {"total": 0, "limite": limite, "percentual": 0, "excedeu": False}
        
    # Pega o mês mais recente no dataframe
    ultimo_mes = resumo_mensal.sort_values(["ano", "mes"], ascending=False).iloc[0]
    total = ultimo_mes["valor_liquido"]
    # Bug Hunt: Proteção contra divisão por zero no limite
    percentual = (total / limite * 100) if limite > 0 else 0
    
    return {
        "ano": int(ultimo_mes["ano"]),
        "mes": int(ultimo_mes["mes"]),
        "total": total,
        "limite": limite,
        "percentual": round(percentual, 2),
        "excedeu": total > limite if limite > 0 else False
    }

def analyze_marketing_costs(df: pd.DataFrame) -> float:
    """
    Isola e soma gastos específicos com marketing/divulgação.
    """
    # Bug Hunt: Busca completa em termos de marketing
    regex_marketing = "|".join([
        "DIVULGAÇÃO", "PROPAGANDA", "PUBLICIDADE", "MARKETING", "COMUNICAÇÃO"
    ])
    mask = df["categoria"].str.contains(regex_marketing, case=False, na=False)
    return float(df[mask]["valor_liquido"].sum())

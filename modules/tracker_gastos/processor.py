"""
Processador de dados de despesas usando Pandas.
Responsável por limpeza, tipagem e agregações dos dados brutos da API.
"""

import pandas as pd


def clean_expenses(data: list[dict]) -> pd.DataFrame:
    """
    Converte a lista de dicionários em DataFrame limpo e tipado.

    Args:
        data: Lista de dicionários retornada pela API.

    Returns:
        DataFrame limpo com colunas devidamente tipadas.
    """
    if not data:
        print("[processor] Nenhum dado de despesa recebido.")
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # --- Renomear colunas para nomes mais legíveis (PT-BR) ---
    rename_map = {
        "ano": "ano",
        "mes": "mes",
        "tipoDespesa": "categoria",
        "codDocumento": "cod_documento",
        "tipoDocumento": "tipo_documento",
        "codTipoDocumento": "cod_tipo_documento",
        "dataDocumento": "data_documento",
        "numDocumento": "num_documento",
        "valorDocumento": "valor_documento",
        "urlGlosa": "url_glosa",
        "nomeFornecedor": "fornecedor",
        "cnpjCpfFornecedor": "cnpj_cpf_fornecedor",
        "valorLiquido": "valor_liquido",
        "valorGlosa": "valor_glosa",
        "numRessarcimento": "num_ressarcimento",
        "codLote": "cod_lote",
        "parcela": "parcela",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # --- Tratamento de tipos ---
    if "valor_documento" in df.columns:
        df["valor_documento"] = pd.to_numeric(df["valor_documento"], errors="coerce").fillna(0.0)

    if "valor_liquido" in df.columns:
        df["valor_liquido"] = pd.to_numeric(df["valor_liquido"], errors="coerce").fillna(0.0)

    if "valor_glosa" in df.columns:
        df["valor_glosa"] = pd.to_numeric(df["valor_glosa"], errors="coerce").fillna(0.0)

    if "data_documento" in df.columns:
        df["data_documento"] = pd.to_datetime(df["data_documento"], errors="coerce")

    if "mes" in df.columns:
        df["mes"] = pd.to_numeric(df["mes"], errors="coerce").fillna(0).astype(int)

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce").fillna(0).astype(int)

    # --- Tratar valores nulos em texto ---
    colunas_texto = ["categoria", "fornecedor", "tipo_documento", "cnpj_cpf_fornecedor"]
    for col in colunas_texto:
        if col in df.columns:
            df[col] = df[col].fillna("NÃO INFORMADO").str.strip()

    # --- Remover duplicatas ---
    linhas_antes = len(df)
    if "cod_documento" in df.columns:
        df = df.drop_duplicates(subset=["cod_documento"])
        removidas = linhas_antes - len(df)
        if removidas > 0:
            print(f"[processor] {removidas} duplicatas removidas.")

    print(f"[processor] DataFrame limpo: {len(df)} registros, {len(df.columns)} colunas.")
    return df


def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega despesas por mês e categoria, calculando totais.

    Args:
        df: DataFrame limpo de despesas.

    Returns:
        DataFrame com soma mensal por categoria.
    """
    if df.empty:
        return pd.DataFrame()

    colunas_necessarias = {"ano", "mes", "categoria", "valor_liquido"}
    if not colunas_necessarias.issubset(df.columns):
        missing = colunas_necessarias - set(df.columns)
        print(f"[processor] Colunas ausentes para agregação: {missing}")
        return pd.DataFrame()

    agregado = (
        df.groupby(["ano", "mes", "categoria"], as_index=False)
        .agg(
            total_gasto=("valor_liquido", "sum"),
            num_transacoes=("valor_liquido", "count"),
            maior_despesa=("valor_liquido", "max"),
        )
        .sort_values(["ano", "mes", "total_gasto"], ascending=[True, True, False])
        .reset_index(drop=True)
    )

    print(f"[processor] Agregação mensal: {len(agregado)} categorias/meses.")
    return agregado


def aggregate_by_supplier(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Top N fornecedores por valor líquido total.

    Args:
        df: DataFrame limpo de despesas.
        top_n: Quantidade de fornecedores a retornar.

    Returns:
        DataFrame com os maiores fornecedores.
    """
    if df.empty or "fornecedor" not in df.columns:
        return pd.DataFrame()

    return (
        df.groupby("fornecedor", as_index=False)
        .agg(total_pago=("valor_liquido", "sum"), num_notas=("valor_liquido", "count"))
        .sort_values("total_pago", ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )

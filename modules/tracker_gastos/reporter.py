"""
Exportador de relatórios para CSV e Parquet.
"""

import os
import pandas as pd
from pathlib import Path

from .config import OUTPUT_DIR


def _ensure_dir(path: str) -> None:
    """Garante que o diretório de destino existe."""
    Path(path).mkdir(parents=True, exist_ok=True)


def export_csv(df: pd.DataFrame, filename: str, output_dir: str = OUTPUT_DIR) -> str:
    """
    Exporta DataFrame para arquivo CSV.

    Args:
        df: DataFrame a exportar.
        filename: Nome do arquivo (sem extensão).
        output_dir: Diretório de destino.

    Returns:
        Caminho absoluto do arquivo gerado.
    """
    _ensure_dir(output_dir)
    filepath = os.path.join(output_dir, f"{filename}.csv")
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"[reporter] CSV exportado → {filepath}")
    return filepath


def export_parquet(df: pd.DataFrame, filename: str, output_dir: str = OUTPUT_DIR) -> str:
    """
    Exporta DataFrame para arquivo Parquet (formato binário eficiente).

    Args:
        df: DataFrame a exportar.
        filename: Nome do arquivo (sem extensão).
        output_dir: Diretório de destino.

    Returns:
        Caminho absoluto do arquivo gerado.
    """
    _ensure_dir(output_dir)
    filepath = os.path.join(output_dir, f"{filename}.parquet")
    df.to_parquet(filepath, index=False, engine="pyarrow")
    print(f"[reporter] Parquet exportado → {filepath}")
    return filepath


def print_summary(df: pd.DataFrame, titulo: str = "Resumo das Despesas") -> None:
    """
    Imprime um resumo estatístico no terminal.

    Args:
        df: DataFrame de despesas agregadas.
        titulo: Título do resumo.
    """
    print(f"\n{'='*60}")
    print(f"  {titulo}")
    print(f"{'='*60}")
    if df.empty:
        print("  Nenhum dado disponível.")
        return

    if "total_gasto" in df.columns:
        total_geral = df["total_gasto"].sum()
        print(f"  💰 Total Geral:       R$ {total_geral:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        print(f"  📊 Categorias:        {df['categoria'].nunique() if 'categoria' in df.columns else 'N/A'}")
        print(f"  📅 Período:")
        if "ano" in df.columns and "mes" in df.columns:
            print(f"     De: {df['mes'].min():02d}/{df['ano'].min()}")
            print(f"     Até: {df['mes'].max():02d}/{df['ano'].max()}")
        print(f"\n  Top 3 Categorias por Gasto:")
        if "categoria" in df.columns:
            top3 = df.groupby("categoria")["total_gasto"].sum().nlargest(3)
            for cat, val in top3.items():
                val_fmt = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                print(f"    • {cat}: R$ {val_fmt}")
    print(f"{'='*60}\n")

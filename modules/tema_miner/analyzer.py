"""
Analisador de frequência de termos para identificar pautas legislativas.
"""

from collections import Counter


def count_frequencies(tokens: list[str]) -> Counter:
    """
    Conta a frequência de cada termo na lista de tokens.

    Args:
        tokens: Lista de tokens limpos e filtrados.

    Returns:
        Counter com {termo: frequência}.
    """
    counter = Counter(tokens)
    print(f"[analyzer] {len(counter)} termos únicos encontrados.")
    return counter


def get_top_terms(counter: Counter, n: int = 20) -> list[tuple[str, int]]:
    """
    Retorna os N termos mais frequentes.

    Args:
        counter: Counter de frequências.
        n: Número de termos a retornar.

    Returns:
        Lista de (termo, frequência) ordenada do maior para menor.
    """
    top = counter.most_common(n)
    print(f"\n[analyzer] Top {n} termos mais frequentes:")
    for i, (termo, freq) in enumerate(top, 1):
        barra = "█" * min(int(freq / max(counter.values()) * 40), 40)
        print(f"  {i:2}. {termo:<25} {freq:>5}  {barra}")
    return top


def get_term_stats(counter: Counter) -> dict:
    """
    Calcula estatísticas gerais sobre os termos.

    Args:
        counter: Counter de frequências.

    Returns:
        Dicionário com estatísticas.
    """
    if not counter:
        return {}

    frequencias = list(counter.values())
    return {
        "total_tokens": sum(frequencias),
        "termos_unicos": len(counter),
        "termo_mais_frequente": counter.most_common(1)[0] if counter else None,
        "media_frequencia": sum(frequencias) / len(frequencias),
        "frequencia_maxima": max(frequencias),
    }

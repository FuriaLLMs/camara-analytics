"""
Limpeza e pré-processamento de texto para NLP.
Aplica expressões regulares e remoção de stopwords em PT-BR com NLTK.
"""

import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download automático dos recursos NLTK necessários
def _ensure_nltk_resources() -> None:
    """Garante que os recursos NLTK estejam disponíveis."""
    resources = [
        ("tokenizers/punkt", "punkt"),
        ("tokenizers/punkt_tab", "punkt_tab"),
        ("corpora/stopwords", "stopwords"),
    ]
    for path, name in resources:
        try:
            nltk.data.find(path)
        except LookupError:
            print(f"[tema_miner] Baixando recurso NLTK: {name}...")
            nltk.download(name, quiet=True)


_ensure_nltk_resources()


# Stopwords em PT-BR (NLTK) + termos legislativos sem valor semântico
_STOPWORDS_EXTRA = {
    "art", "lei", "nº", "§", "dispõe", "estabelece", "altera",
    "acrescenta", "revoga", "dá", "institui", "cria", "disposto",
    "conforme", "cujo", "respectivo", "referido", "nos", "às",
    "ser", "deve", "pode", "seja", "fica", "deste", "desta",
    "através", "mediante", "contida", "demais", "demaia", "inciso",
    "mesa", "diretora", "oficio", "indicação", "redação", "capítulo",
    "título", "constituição", "membro", "ementa", "federal", "pública",
    "nacional", "parágrafo", "seguinte", "forma", "termos", "sobre",
    "outras", "providências", "artigo", "leis", "diretrizes", "bases",
    "alínea", "item", "incisos", "anexo", "único", "caput", "parágrafos",
}


def _get_stopwords() -> set[str]:
    """Retorna conjunto completo de stopwords PT-BR."""
    sw = set(stopwords.words("portuguese"))
    sw.update(_STOPWORDS_EXTRA)
    return sw


def clean_text(text: str) -> str:
    """
    Aplica pipeline de limpeza de texto legislativo com regex:
    1. Lowercase
    2. Remove números e ordinals (1º, 2ª, etc.)
    3. Remove pontuação
    4. Remove espaços extras

    Args:
        text: Texto bruto da ementa.

    Returns:
        Texto limpo.
    """
    # Lowercase
    text = text.lower()

    # Remover números e ordinals (ex: 1º, 2ª, art. 3)
    text = re.sub(r"\b\d+[ºª°]?\b", "", text)

    # Remover URLs
    text = re.sub(r"https?://\S+", "", text)

    # Remover pontuação e caracteres especiais
    text = re.sub(r"[^\w\sàáâãäéèêíîóôõöúüçñ]", " ", text)

    # Remover espaços extras
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize_and_filter(text: str, min_length: int = 4) -> list[str]:
    """
    Tokeniza o texto e remove stopwords e tokens curtos.

    Args:
        text: Texto limpo (saída de clean_text).
        min_length: Tamanho mínimo de um token para ser mantido.

    Returns:
        Lista de tokens filtrados.
    """
    sw = _get_stopwords()

    try:
        tokens = word_tokenize(text, language="portuguese")
    except Exception:
        # Fallback para split simples
        tokens = text.split()

    tokens_filtrados = [
        t for t in tokens
        if len(t) >= min_length
        and t not in sw
        and t not in string.punctuation
        and not t.startswith("_")
    ]

    return tokens_filtrados


def remove_stopwords(tokens: list[str]) -> list[str]:
    """
    Remove stopwords de uma lista de tokens já tokenizados.

    Args:
        tokens: Lista de tokens.

    Returns:
        Lista sem stopwords.
    """
    sw = _get_stopwords()
    return [t for t in tokens if t not in sw]


def process_ementas(ementas: list[str]) -> list[str]:
    """
    Pipeline completo: limpa e tokeniza uma lista de ementas.

    Args:
        ementas: Lista de textos brutos.

    Returns:
        Lista plana de todos os tokens.
    """
    todos_tokens: list[str] = []
    for ementa in ementas:
        texto_limpo = clean_text(ementa)
        tokens = tokenize_and_filter(texto_limpo)
        todos_tokens.extend(tokens)

    print(f"[tema_miner] {len(todos_tokens)} tokens extraídos de {len(ementas)} ementas.")
    return todos_tokens

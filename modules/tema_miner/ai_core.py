"""
Módulo central de Inteligência Artificial e NLP para análise legislativa.
Integra modelos locais (NLTK) e APIs de LLMs (v4.0).
"""

import re
import nltk
from typing import Dict, List, Optional

# Garantir recursos do NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class AICore:
    """Core de IA para processamento de textos da Câmara."""

    @staticmethod
    def calcular_indice_complexidade(texto: str) -> Dict[str, float]:
        """
        Calcula o Índice de Legibilidade de Flesch adaptado para o Português.
        Fórmula: 248.835 - (1.015 * media_palavras_por_frase) - (84.6 * media_silabas_por_palavra)
        """
        if not texto or len(texto.strip()) < 10:
            return {"score": 0.0, "nivel": "N/A"}

        sentencas = nltk.sent_tokenize(texto)
        palavras = [p for p in nltk.word_tokenize(texto) if p.isalnum()]
        
        if not palavras or not sentencas:
            return {"score": 0.0, "nivel": "N/A"}

        def contar_silabas(palavra: str) -> int:
            # Heurística simples para contagem de sílabas em PT
            palavra = palavra.lower()
            return len(re.findall(r'[aeiouáéíóúâêîôûãõ]', palavra))

        num_palavras = len(palavras)
        num_sentencas = len(sentencas)
        num_silabas = sum(contar_silabas(p) for p in palavras)

        asl = num_palavras / num_sentencas  # Average Sentence Length
        asw = num_silabas / num_palavras   # Average Syllables per Word

        flesch = 248.835 - (1.015 * asl) - (84.6 * asw)
        
        # Interpretação
        if flesch > 75: nivel = "Muito Fácil"
        elif flesch > 60: nivel = "Fácil"
        elif flesch > 50: nivel = "Razoável"
        elif flesch > 30: nivel = "Difícil"
        else: nivel = "Muito Difícil (Acadêmico/Jurídico)"

        return {
            "score": round(flesch, 2),
            "nivel": nivel,
            "palavras": num_palavras,
            "sentencas": num_sentencas
        }

    @staticmethod
    def analisar_sentimento_llm(texto: str) -> str:
        """
        (Placeholder para Chamada de API)
        Analisa se o discurso é Técnico, Agressivo ou Conciliador.
        """
        # TODO: Implementar integração com Gemini ou OpenAI
        return "Técnico (Análise Local Indisponível)"

    @staticmethod
    def sumarizar_pl_llm(ementa: str, texto_integral: Optional[str] = None) -> str:
        """
        (Placeholder para Chamada de API)
        Resume um Projeto de Lei em linguagem simples.
        """
        # TODO: Implementar integração com LLM
        return ementa # Retorna a ementa original por enquanto

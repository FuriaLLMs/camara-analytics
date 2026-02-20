# v4.1.2 - Forçando detecção de arquivos
import os
import re
import nltk
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Carregar variáveis de ambiente
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Garantir recursos do NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class AICore:
    """Core de IA para processamento de textos da Câmara."""

    @staticmethod
    def _call_gemini(prompt: str) -> str:
        """Helper para chamadas seguras ao Gemini."""
        if not GOOGLE_API_KEY:
            return "Indisponível (Sem Chave)"
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Erro na IA: {str(e)[:50]}"

    @staticmethod
    def calcular_indice_complexidade(texto: str) -> Dict[str, float]:
        """
        Calcula o Índice de Legibilidade de Flesch adaptado para o Português.
        """
        if not texto or len(texto.strip()) < 10:
            return {"score": 0.0, "nivel": "N/A"}

        sentencas = nltk.sent_tokenize(texto)
        palavras = [p for p in nltk.word_tokenize(texto) if p.isalnum()]
        
        if not palavras or not sentencas:
            return {"score": 0.0, "nivel": "N/A"}

        def contar_silabas(palavra: str) -> int:
            palavra = palavra.lower()
            return len(re.findall(r'[aeiouáéíóúâêîôûãõ]', palavra))

        num_palavras = len(palavras)
        num_sentencas = len(sentencas)
        num_silabas = sum(contar_silabas(p) for p in palavras)

        asl = num_palavras / num_sentencas 
        asw = num_silabas / num_palavras   

        flesch = 248.835 - (1.015 * asl) - (84.6 * asw)
        
        if flesch > 75: nivel = "Muito Fácil"
        elif flesch > 60: nivel = "Fácil"
        elif flesch > 50: nivel = "Razoável"
        elif flesch > 30: nivel = "Difícil"
        else: nivel = "Muito Difícil (Jurídico)"

        return {
            "score": round(flesch, 2),
            "nivel": nivel,
            "palavras": num_palavras,
            "sentencas": num_sentencas
        }

    @staticmethod
    def analisar_sentimento_llm(texto: str) -> str:
        """Analisa se o discurso é Técnico, Agressivo ou Conciliador via Gemini."""
        if not texto: return "N/A"
        
        prompt = f"""
        Analise o tom predominante do seguinte discurso parlamentar. 
        Responda APENAS com uma das três palavras: 'Técnico', 'Agressivo' ou 'Conciliador'.
        
        Discurso: "{texto[:2000]}"
        """
        return AICore._call_gemini(prompt)

    @staticmethod
    def sumarizar_perfil_llm(tokens: List[str]) -> str:
        """Gera uma frase resumindo o foco do parlamentar baseado em termos-chave."""
        if not tokens: return "Sem dados de produção."
        
        prompt = f"""
        Baseado nestas palavras-chave de um parlamentar brasileiro, descreva o foco principal dele em UMA FRASE curta de no máximo 15 palavras.
        Termos: {', '.join(tokens[:30])}
        """
        return AICore._call_gemini(prompt)

    @staticmethod
    def traduzir_politiques(ementa: str) -> str:
        """Converte linguagem técnica jurídica em linguagem cidadã simples."""
        if not ementa: return ""
        
        prompt = f"""
        Traduza a seguinte ementa legislativa para o 'Cidadão Comum'. 
        Seja curto e direto. Remova termos como 'Altera a lei X' ou 'Dispõe sobre Y'.
        
        Ementa: {ementa}
        """
        return AICore._call_gemini(prompt)

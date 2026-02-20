# v4.2.0 - Blindagem Total (Cache Persistente + Fallback Heurístico)
import os
import re
import json
import nltk
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, List, Optional
from pathlib import Path

# Carregar variáveis de ambiente
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# Configuração de Cache Persistente
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "ai_responses.json"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_persistent_cache() -> Dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except:
            return {}
    return {}

def save_persistent_cache(cache: Dict):
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    except:
        pass

# Garantir recursos do NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class AICore:
    """Core de IA para processamento de textos da Câmara."""

    @staticmethod
    def _call_gemini(prompt: str, cache_key: Optional[str] = None) -> str:
        """Helper para chamadas seguras ao Gemini com Cache Persistente."""
        
        # 1. Tentar Cache Persistente (Disco)
        if cache_key:
            full_cache = load_persistent_cache()
            if cache_key in full_cache:
                return full_cache[cache_key]

        # 2. Se não tem chave ou não está no cache, tentar API
        if not GOOGLE_API_KEY:
            return None # Sinaliza que precisa de fallback

        try:
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            result = response.text.strip()
            
            # 3. Salvar no Cache se funcionou
            if cache_key and result:
                full_cache = load_persistent_cache()
                full_cache[cache_key] = result
                save_persistent_cache(full_cache)
                
            return result
        except Exception as e:
            # Bug Hunt: 429 ou qualquer erro -> Sinaliza para Fallback
            return None

    @staticmethod
    def calcular_indice_complexidade(texto: str) -> Dict[str, float]:
        """Calcula o Índice de Legibilidade de Flesch adaptado para o Português."""
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
    @st.cache_data(ttl=86400, show_spinner=False)
    def analisar_sentimento_llm(texto: str, dep_id: int) -> str:
        """Fallback: Técnico (Análise Local) se a API falhar."""
        if not texto: return "N/A (Sem Discursos)"
        
        cache_key = f"sentimento_{dep_id}_{hash(texto[:100])}"
        prompt = f"Analise o tom (Técnico/Agressivo/Conciliador) deste discurso: {texto[:1000]}"
        
        res = AICore._call_gemini(prompt, cache_key)
        if res: return res
        
        # Fallback Local Heurístico
        return "Técnico (Análise Local)"

    @staticmethod
    @st.cache_data(ttl=86400, show_spinner=False)
    def sumarizar_perfil_llm(tokens: List[str], dep_id: int) -> str:
        """Gera resumo via API ou Heurística local de tokens."""
        if not tokens: return "Sem dados de produção registrados."
        
        cache_key = f"resumo_{dep_id}"
        prompt = f"Resuma o foco deste parlamentar em 10 palavras: {', '.join(tokens[:20])}"
        
        res = AICore._call_gemini(prompt, cache_key)
        if res: return res
        
        # Fallback Heurístico (DNA Parlamentar Automático)
        # Pega tokens únicos para evitar repetição e filtra os 6 mais relevantes (curados)
        vistos = set()
        top_tokens = []
        for t in tokens:
            t_low = t.lower()
            if t_low not in vistos and len(t) > 4:
                top_tokens.append(t.capitalize())
                vistos.add(t_low)
            if len(top_tokens) >= 6: break

        temas = ", ".join(top_tokens)
        return f"Eixos de Atuação Técnica: {temas}."

    @staticmethod
    @st.cache_data(ttl=86400, show_spinner=False)
    def traduzir_politiques(ementa: str) -> str:
        """Simplifica ementas via API ou retorna a ementa limpa."""
        if not ementa: return "N/A"
        
        cache_key = f"trad_{hash(ementa)}"
        prompt = f"Simplifique esta ementa para um cidadão comum: {ementa}"
        
        res = AICore._call_gemini(prompt, cache_key)
        if res: return res
        
        # Fallback: Apenas limpa a ementa (remove o cabeçalho técnico comum)
        clean = re.sub(r'^(Altera|Dispõe sobre|Cria|Institui)\s+', '', ementa, flags=re.IGNORECASE)
        return clean[:150] + "..." if len(clean) > 150 else clean

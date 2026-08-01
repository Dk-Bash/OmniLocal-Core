"""
Utilidades de texto para búsqueda por palabras clave.

La base LIKE de SQLite solo encuentra coincidencias si la frase completa
buscada aparece tal cual en el contenido. Eso hace que "¿Cómo te llamás?"
nunca encuentre nada guardado como "mi nombre es Marcelo", aunque ambas
frases compartan la palabra clave relevante. Este módulo separa una consulta
en sus palabras significativas para poder buscar por superposición de
palabras en lugar de por coincidencia literal de la frase entera.
"""
import re
from typing import List

# Palabras muy comunes en español que no aportan a la búsqueda.
STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "y", "o", "u", "que", "qué", "como", "cómo", "para", "por", "con", "sin",
    "es", "soy", "eres", "somos", "son", "ser", "estar", "esta", "esto",
    "estas", "estos", "esa", "eso", "ese", "aquel", "aquella", "yo", "tu",
    "tú", "tus", "mi", "mis", "su", "sus", "me", "te", "se", "nos", "les",
    "le", "lo", "muy", "más", "menos", "todo", "toda", "todos", "todas",
    "hoy", "ya", "no", "si", "sí", "en", "a", "e", "antes", "despues",
    "después", "cual", "cuál", "cuando", "cuándo", "donde", "dónde", "quien",
    "quién", "porque", "pero", "hay", "he", "ha", "han", "fue", "era",
}


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extrae las palabras significativas de un texto: minúsculas, sin
    puntuación, sin stopwords, sin duplicados, preservando el orden.
    """
    words = re.findall(r"[a-záéíóúñü0-9]+", (text or "").lower())
    seen = set()
    keywords = []
    for w in words:
        if len(w) < min_length or w in STOPWORDS or w in seen:
            continue
        seen.add(w)
        keywords.append(w)
    return keywords

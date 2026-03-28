import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Układ strony i tytuł
st.set_page_config(page_title="AI Agent Badawczy", page_icon="🤖", layout="centered")

st.title("🤖 Agent ds. Analizy Rynku i Cen")
st.write("Wpisz nazwę firmy (np. *Notion*) lub kategorię (np. *platformy streamingowe*), a AI wygeneruje przejrzysty raport z tabelą na bazie aktualnych danych z sieci.")

# Wczytanie kluczy
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

if not GEMINI_KEY or not TAVILY_KEY:
    st.error("Błąd: Brak kluczy API w pliku .env")
    st.stop()

client = genai.Client(api_key=GEMINI_KEY)

# ============================================================
# NARZĘDZIA (Skopiowane z Twojego agent.py)
# ============================================================
def search_web(query: str) -> str:
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": query, "search_depth": "advanced", "max_results": 4},
            timeout=20
        )
        data = response.json()
        results = [f"URL: {r['url']}\nTreść: {r.get('content', '')[:600]}" for r in data.get("results", [])]
        return "\n---\n".join(results) or "Brak wyników."
    except Exception as e:
        return f"BŁĄD: {str(e)}"

def scrape_page(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]): tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:4000]
    except Exception as e:
        return f"BŁĄD: {str(e)}"

SYSTEM_INSTRUCTION = """Jesteś ekspertem ds. badań rynkowych i analitykiem cenowym.
Twoim zadaniem jest analiza cenowa firm LUB całych kategorii produktów.
ZASADY KRYTYCZNE:
- ZAWSZE podawaj źródła (URL).
- ZAWSZE wygeneruj tabelę z porównaniem cen.
FORMAT: Używaj poprawnego języka Markdown do tworzenia nagłówków i tabel."""

# ============================================================
# INTERFEJS UŻYTKOWNIKA (FRONTEND)
# ============================================================

# Pole tekstowe dla użytkownika
topic = st.text_input("Czego szukasz dzisiaj?", placeholder="np. CRM dla małych firm...")

# Przycisk uruchamiający
if st.button("Generuj Raport", type="primary"):
    if not topic:
        st.warning("Proszę wpisać temat przed kliknięciem!")
    else:
        # Pasek ładowania kręci się, póki agent pracuje
        with st.spinner("Przeszukuję internet i analizuję dane. To może zająć 20-30 sekund..."):
            try:
                chat = client.chats.create(
                    model="gemini-2.5-flash", 
                    config=types.GenerateContentConfig(
                        tools=[search_web, scrape_page],
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.2
                    )
                )
                
                prompt = f"Przeanalizuj temat: **{topic}**. Użyj narzędzi, zbierz dane i wygeneruj pełny raport Markdown z tabelami."
                response = chat.send_message(prompt)
                
                st.success("Raport gotowy!")
                
                # Wyświetlenie pięknego raportu z tabelami na stronie!
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Wystąpił błąd: {e}")
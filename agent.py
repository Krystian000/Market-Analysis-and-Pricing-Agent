import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# ============================================================
# 1. KONFIGURACJA APLIKACJI (Zawsze na samej górze)
# ============================================================
st.set_page_config(
    page_title="Market Intelligence AI", 
    page_icon="📊", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# 2. AUTORYZACJA I ZARZĄDZANIE KLUCZAMI
# ============================================================
# Pobieramy klucze z chmury Streamlit (Secrets) lub z pliku lokalnego (.env)
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
TAVILY_KEY = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY"))

if not GEMINI_KEY or not TAVILY_KEY:
    st.error("🚨 **Błąd krytyczny:** Brak kluczy API. Dodaj GEMINI_API_KEY oraz TAVILY_API_KEY w zakładce 'Secrets' na Streamlit Cloud.")
    st.stop() # Zatrzymuje aplikację, żeby nie generowała kolejnych błędów

# Inicjalizacja klienta tylko raz
client = genai.Client(api_key=GEMINI_KEY)

# ============================================================
# 3. ZOPTYMALIZOWANE NARZĘDZIA DLA AI
# ============================================================
def search_web(query: str) -> str:
    """Wyszukuje informacje w sieci za pomocą Tavily API."""
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": query, "search_depth": "advanced", "max_results": 4},
            timeout=15
        )
        response.raise_for_status() # Wyrzuci błąd, jeśli API nie odpowie
        
        results = response.json().get("results", [])
        formatted_results = [f"Źródło: {r['url']}\nFragment: {r.get('content', '')[:800]}" for r in results]
        
        return "\n---\n".join(formatted_results) if formatted_results else "Brak wyników."
    except Exception as e:
        return f"BŁĄD WYSZUKIWANIA: {str(e)}"

def scrape_page(url: str) -> str:
    """Pobiera czysty tekst ze strony internetowej."""
    try:
        # Bardziej realistyczne nagłówki, by ominąć proste blokady anty-bot
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,pl;q=0.8"
        }
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Usuwamy elementy niepotrzebne do analizy tekstu
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]): 
            tag.decompose()
            
        text = soup.get_text(separator=" ", strip=True)
        return text[:4500] # Ograniczamy do 4500 znaków (optymalne dla kontekstu API)
    except Exception as e:
        return f"BŁĄD SKRAPOWANIA ({url}): {str(e)}"

# ============================================================
# 4. SILNIK AGENTA (Z pamięcią podręczną - Cache)
# ============================================================
SYSTEM_INSTRUCTION = """Jesteś analitykiem biznesowym (Market Intelligence).
Twoim zadaniem jest analiza cen firm lub całych kategorii rynkowych.
ZASADY:
1. MUSISZ tworzyć czytelne tabele porównawcze.
2. MUSISZ podawać w nawiasach źródła danych w formie (Źródło: URL).
3. Pisz w sposób profesjonalny, konkretny, używając języka Markdown.
4. Zwróć uwagę na ukryte koszty i haczyki w cennikach."""

# @st.cache_data sprawia, że pytania o ten sam temat nie zużywają limitów API
@st.cache_data(ttl=3600, show_spinner=False)
def generate_market_report(topic: str) -> str:
    """Główna funkcja orkiestrująca AI, korzystająca z cache na 1 godzinę."""
    chat = client.chats.create(
        model="gemini-2.5-flash", 
        config=types.GenerateContentConfig(
            tools=[search_web, scrape_page],
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1 # Niska temperatura = bardziej precyzyjne, mniej "halucynujące" dane
        )
    )
    
    prompt = f"Przeprowadź głęboki research i stwórz profesjonalny raport cenowy w Markdown dla: **{topic}**. Użyj dostępnych narzędzi."
    response = chat.send_message(prompt)
    return response.text

# ============================================================
# 5. FRONTEND (Interfejs Użytkownika)
# ============================================================
st.title("📊 AI Market Intelligence Agent")
st.markdown("Wpisz interesującą Cię branżę lub firmę, a agent samodzielnie przeszuka sieć, przeczyta cenniki i wygeneruje przejrzysty raport.")

# Używamy formularza, żeby uniknąć przypadkowych odświeżeń strony
with st.form(key="search_form"):
    topic_input = st.text_input(
        "Temat analizy (firma lub kategoria):", 
        placeholder="np. systemy CRM dla e-commerce, Netflix vs HBO..."
    )
    submit_button = st.form_submit_button(label="🚀 Wygeneruj Raport", use_container_width=True)

# Logika po kliknięciu przycisku
if submit_button:
    if len(topic_input.strip()) < 2:
        st.warning("Wpisz poprawny temat do przeanalizowania.")
    else:
        with st.spinner(f"🔍 Trwa badanie rynku dla: '{topic_input}'. To zajmie kilkanaście sekund..."):
            try:
                # Wywołanie zoptymalizowanej, cachowanej funkcji
                report_content = generate_market_report(topic_input)
                
                st.success("✅ Raport został wygenerowany pomyślnie!")
                
                # Zgrabny kontener na wynik, by odróżniał się wizualnie
                with st.container(border=True):
                    st.markdown(report_content)
                    
            except Exception as e:
                st.error(f"❌ Niestety wystąpił problem techniczny: {str(e)}")
                st.info("Spróbuj sformułować zapytanie inaczej lub poczekaj chwilę przed kolejną próbą.")

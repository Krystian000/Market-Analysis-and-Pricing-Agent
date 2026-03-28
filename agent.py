import os
import sys
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown


from google import genai
from google.genai import types

# Wczytaj klucze
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

if not GEMINI_KEY or not TAVILY_KEY:
    print("BŁĄD: Brak kluczy w pliku .env (sprawdź GEMINI_API_KEY i TAVILY_API_KEY)")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_KEY)

# ============================================================
# NARZĘDZIA AGENTA
# ============================================================

def search_web(query: str) -> str:
    """Wyszukaj w internecie aktualne informacje o firmach, produktach i cenach."""
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": TAVILY_KEY, 
                "query": query, 
                "search_depth": "advanced",
                "max_results": 4
            },
            timeout=20
        )
        data = response.json()
        results = [f"URL: {r['url']}\nTreść: {r.get('content', '')[:600]}" for r in data.get("results", [])]
        return "\n---\n".join(results) or "Brak wyników wyszukiwania."
    except Exception as e:
        return f"BŁĄD wyszukiwania: {str(e)}"

def scrape_page(url: str) -> str:
    """Pobierz dokładną treść strony internetowej (np. z cennikiem)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]): 
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:4000]
    except Exception as e:
        return f"BŁĄD pobierania strony: {str(e)}"

# ============================================================
# SYSTEM PROMPT — "DNA" AGENTA (ZMODYFIKOWANE)
# ============================================================

SYSTEM_INSTRUCTION = """Jesteś ekspertem ds. badań rynkowych i analitykiem cenowym.
Twoim zadaniem jest analiza cenowa konkretnych firm LUB całych kategorii produktów/usług.

JAK MASZ DZIAŁAĆ:
1. Rozpoznaj intencję użytkownika:
   - Jeśli to KATEGORIA (np. "filmy i seriale", "CRM", "narzędzia do księgowości"):
     Najpierw wyszukaj 3-4 najpopularniejsze serwisy/firmy w tej kategorii, a potem znajdź i porównaj ich ceny.
   - Jeśli to KONKRETNA FIRMA (np. "Netflix", "Notion"):
     Znajdź jej szczegółowy cennik, a następnie wyszukaj jej głównych konkurentów, by zrobić porównanie.

ZASADY KRYTYCZNE:
- ZAWSZE podawaj źródła dla cen w formacie: (Źródło: URL).
- ZAWSZE wygeneruj tabelę z porównaniem cen i funkcji.
- Samodzielnie decyduj, jakich zapytań (queries) użyć w wyszukiwarce. Bądź dociekliwy.
- Korzystaj z polskic cenników, preferuj oficjalne strony firm, jeśli nie znajdziesz szukaj też zagranicznych, ale spróbuj je przewalutować na PLN.

FORMAT RAPORTU (Markdown):

# Analiza Rynku / Cen: [Temat]
**Data wygenerowania:** [Dzisiejsza data]

## 💡 Podsumowanie Rynku
[Krótki opis: jacy są główni gracze w tej kategorii lub z kim konkuruje podana firma]

## 💰 Zestawienie Ofert (Tabela)
| Firma/Usługa | Plan | Cena/mies | Główne cechy/limity | Źródło |
|--------------|------|-----------|---------------------|--------|
| ...          | ...  | ...       | ...                 | ...    |

## 🕵️ Ukryte koszty i haczyki
[Na co uważać? Np. opłaty za współdzielenie konta, reklamy w tanich planach, umowy roczne itp.]

## ⚖️ Werdykt: Co i dla kogo?
[Napisz, co wychodzi najtaniej, a co oferuje najwyższą jakość / premium]

## 🔗 Źródła
[Lista linków z których korzystałeś]
"""

# ============================================================
# GŁÓWNA PĘTLA
# ============================================================

def run_agent(topic: str):
    today = datetime.now().strftime("%d.%m.%Y")
    
    print(f"\n{'='*55}")
    print(f"  🤖 Agent Badawczy (Gemini) analizuje: {topic}")
    print(f"{'='*55}\n")

    chat = client.chats.create(
        model="gemini-2.5-flash", 
        config=types.GenerateContentConfig(
            tools=[search_web, scrape_page],
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2
        )
    )
    
    # Zmieniliśmy prompt na bardziej otwarty, dając agentowi wolną rękę w działaniu
    prompt = (
        f"Przeanalizuj temat: **{topic}**. Dzisiejsza data to {today}.\n"
        "Samodzielnie używaj narzędzi (search_web, scrape_page) w optymalnej kolejności. "
        "Zbierz solidne dane i wygeneruj pełny raport Markdown zgodnie z System Instruction."
    )

    try:
        print("Trwa zbieranie danych i badanie rynku (to może zająć 20-30 sekund)...\n")
        response = chat.send_message(prompt)
        
        os.makedirs("output", exist_ok=True)
        safe_name = topic.replace(" ", "_").replace("/", "-")
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"output/{safe_name}_Gemini_{date_str}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)

        print(f"✅ GOTOWE! Raport zapisany: {filename}")
        print(f"\n{'='*55}\nPODGLĄD RAPORTU:\n{'='*55}\n")
        print(f"✅ GOTOWE! Raport zapisany: {filename}")
        print(f"\n{'='*55}\nPODGLĄD RAPORTU:\n{'='*55}\n")
        
        # Magia biblioteki Rich - rysuje piękne tabele w terminalu!
        console = Console()
        md = Markdown(response.text)
        console.print(md)

    except Exception as e:
        print(f"❌ Wystąpił błąd podczas działania agenta: {e}")
        







    except Exception as e:
        print(f"❌ Wystąpił błąd podczas działania agenta: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nJak używać w terminalu:")
        print("  python agent.py \"Nazwa firmy\"   (np. python agent.py \"Netflix\")")
        print("  python agent.py \"Kategoria\"     (np. python agent.py \"filmy i seriale platformy\")")
        sys.exit(0)

    topic = " ".join(sys.argv[1:])
    run_agent(topic)
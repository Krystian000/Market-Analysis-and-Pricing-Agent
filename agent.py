import streamlit as st
import os
import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# ============================================================
# 1. KONFIGURACJA APLIKACJI
# ============================================================
st.set_page_config(
    page_title="Global Market AI", 
    page_icon="🌍", 
    layout="centered"
)

# Pobieranie kluczy
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))
TAVILY_KEY = st.secrets.get("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY"))

if not GEMINI_KEY or not TAVILY_KEY:
    st.error("🚨 Critical Error: Missing API Keys in Secrets.")
    st.stop()

client = genai.Client(api_key=GEMINI_KEY)

# ============================================================
# 2. NARZĘDZIA DLA AI
# ============================================================
def search_web(query: str) -> str:
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={"api_key": TAVILY_KEY, "query": query, "search_depth": "advanced", "max_results": 4},
            timeout=15
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        formatted_results = [f"Source: {r['url']}\nSnippet: {r.get('content', '')[:800]}" for r in results]
        return "\n---\n".join(formatted_results) if formatted_results else "No results found."
    except Exception as e:
        return f"SEARCH ERROR: {str(e)}"

def scrape_page(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.get(url, headers=headers, timeout=12)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]): 
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:4500]
    except Exception as e:
        return f"SCRAPE ERROR ({url}): {str(e)}"

# ============================================================
# 3. SILNIK AGENTA Z WYMUSZENIEM JĘZYKA I WALUTY
# ============================================================
# Zmienione "DNA" agenta - wymusza angielski i konwersję walut
SYSTEM_INSTRUCTION = """You are a Global Market Intelligence AI.
CRITICAL RULES:
1. ALL your queries to the search engine MUST be in English to find global data.
2. The final report MUST be written entirely in English.
3. You MUST convert all found prices to the user's requested Target Currency.
4. Always provide sources in the format: (Source: URL).
5. Use Markdown to create clean comparison tables."""

@st.cache_data(ttl=3600, show_spinner=False)
def generate_market_report(topic: str, target_currency: str) -> str:
    chat = client.chats.create(
        model="gemini-2.5-flash", 
        config=types.GenerateContentConfig(
            tools=[search_web, scrape_page],
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.1 
        )
    )
    
    # Przekazujemy wybraną walutę do polecenia
    prompt = f"Conduct deep research on: **{topic}**. Output the report in English. IMPORTANT: Convert all pricing data to {target_currency} based on current estimated exchange rates. If you estimate a conversion, briefly mention it."
    
    response = chat.send_message(prompt)
    return response.text

# ============================================================
# 4. FRONTEND (Interfejs w języku angielskim)
# ============================================================
st.title("🌍 Global Market Intelligence AI")
st.markdown("Enter a company or product category. The AI will search the global web and calculate prices into your local currency.")

with st.form(key="search_form"):
    col1, col2 = st.columns([3, 1]) # Dzielimy interfejs na dwie kolumny
    
    with col1:
        topic_input = st.text_input(
            "Topic (Company or Category):", 
            placeholder="e.g. Netflix vs Hulu, Best CRM tools..."
        )
    
    with col2:
        # Rozwijane menu z walutami
        selected_currency = st.selectbox(
            "Target Currency:", 
            ["USD ($)", "EUR (€)", "PLN (zł)", "GBP (£)", "AUD ($)", "CAD ($)"]
        )
        
    submit_button = st.form_submit_button(label="🚀 Generate Report", use_container_width=True)

if submit_button:
    if len(topic_input.strip()) < 2:
        st.warning("Please enter a valid topic.")
    else:
        with st.spinner(f"🔍 Researching global data for '{topic_input}' and converting to {selected_currency}..."):
            try:
                # Przekazujemy temat ORAZ walutę do funkcji
                report_content = generate_market_report(topic_input, selected_currency)
                
                st.success("✅ Report generated successfully!")
                
                with st.container(border=True):
                    st.markdown(report_content)
                    
            except Exception as e:
                st.error(f"❌ Technical issue encountered: {str(e)}")

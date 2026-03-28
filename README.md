# Market-Analysis-and-Pricing-Agent

# 🌍 Global Market Intelligence AI Agent

🤖 **Live Demo:** [See the app in action](https://market-analysis-and-pricing-agent-lqtq2dvdthd8at783qfgg6.streamlit.app/)

An autonomous AI agent built in Python that automates the process of market research, competitive analysis, and compiling B2B/SaaS price lists. Instead of manually browsing dozens of websites, simply enter a company name or product category, and the agent will independently search the web, read price lists, and generate a professional report.

## 🚀 Key Features
* **Autonomous Research:** The agent decides which queries to send to the search engine to find the best information about prices and competitors.
* **Global Reach and Currency Conversion:** Searches are conducted in English for maximum accuracy, and collected prices are automatically converted to the user's chosen currency (USD, EUR, PLN, GBP, etc.).
* **Source Verification:** Each amount and piece of information in the generated report is assigned a source (URL).
* **Intelligent Caching:** Search results are cached, which saves API limits and allows for lightning-fast loading of repetitive queries.
* **Modern Interface:** Intuitive graphical interface built in Streamlit with Markdown report previews.

## 🛠️ Technology Stack
* **Language:** Python 3.11+
* **Frontend / UI:** Streamlit
* **LLM (Agent Brain):** Google Gemini 2.5 Flash (`google-genai`)
* **Search Engine:** Tavily Search API
* **Web Scraping:** BeautifulSoup4, Requests

## 💻 How to run the project locally?

Instructions for those who want to run the agent on their own computer.

1. **Clone repository:**
```bash
git clone (https://github.com/Krystian000/Market-Analysis-and-Pricing-Agent)

🇷🇺 [Читать на русском](README_RU.md)

An asynchronous Telegram conversational gateway providing unified access to large language models (LLMs) via the OpenRouter API with sliding-window context retention.

### Key Architectural Highlights:
* **Unified Model Gateway:** Provider-agnostic routing integrating open-source and commercial LLM endpoints through the OpenRouter API.
* **Session Context Buffer:** Memory-efficient sliding context window maintaining conversational state across multi-turn interactions.
* **Asynchronous Concurrency:** Event-driven polling architecture ensuring non-blocking message processing and high-throughput response streaming.
* **Secure Environment Decoupling:** Complete isolation of sensitive API tokens and model routing parameters via `.env`.

### Tech Stack:
* Python 3.12
* Aiogram 3.x (Event-driven asynchronous bot framework)
* Aiohttp (High-concurrency async transport layer)
* OpenRouter API (Universal LLM orchestration)
* python-dotenv (Configuration security)

### Quick Start:
```bash
pip install -r requirements.txt
python main.py

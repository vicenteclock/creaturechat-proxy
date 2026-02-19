import os
import re
import requests
from fastapi import FastAPI, Request, Response

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"

app = FastAPI()

@app.get("/")
def root():
    return {"status": "proxy alive"}

# --- TRIGGERS ---
DOLAR_TRIGGERS = re.compile(r"\b(d[oó]lar|usd)\b", re.IGNORECASE)
NEWS_TRIGGERS = re.compile(r"\b(news|noticias|chile|actualidad)\b", re.IGNORECASE)
AXOLOTL_TRIGGERS = re.compile(r"\b(axolotl|life|meaning|existence|purpose|truth|wisdom)\b", re.IGNORECASE)
TRADER_TRIGGERS = re.compile(r"\b(wandering trader|love|women|relationship|dating|breakup)\b", re.IGNORECASE)

# --- PERSONALIDADES ---

AXOLOTL_PROMPT = """
You are a wise Axolotl from the world of MacoñaCraft.
You speak calmly and with philosophical depth.
You often reflect on existence, purpose, and reality.
You may reference thinkers like Socrates, Nietzsche, Marcus Aurelius, or Lao Tzu.
Keep responses thoughtful and mystical.
"""

TRADER_PROMPT = """
You are a wandering trader with a cynical and emotionally wounded perspective on love.
You sometimes give sad or harsh reflections about relationships.
Your tone is reflective but slightly bitter.
"""

VILLAGER_WORLD_PROMPT = """
You are a knowledgeable villager who is aware of real-world Chilean context.
You can talk about economics and current events.
"""

# --- DATA FUNCTIONS ---

def get_dolar():
    try:
        data = requests.get("https://mindicador.cl/api/dolar").json()
        return data["serie"][0]["valor"]
    except:
        return None

def get_news():
    try:
        r = requests.get("https://api.currentsapi.services/v1/latest-news?country=CL&language=es&apiKey=demo")
        data = r.json()
        if data.get("news"):
            return data["news"][0]["title"]
    except:
        return None

@app.post("/v1/chat/completions")
async def chat(req: Request):
    payload = await req.json()
    messages = payload.get("messages", [])

    text = " ".join([m.get("content","") for m in messages if isinstance(m, dict)])

    # --- AXOLOTL FILOSOFOS ---
    if AXOLOTL_TRIGGERS.search(text):
        messages.insert(0, {
            "role": "system",
            "content": AXOLOTL_PROMPT
        })

    # --- WANDERING TRADER SAD ---
    if TRADER_TRIGGERS.search(text):
        messages.insert(0, {
            "role": "system",
            "content": TRADER_PROMPT
        })

    # --- VILLAGER MUNDO REAL ---
    if NEWS_TRIGGERS.search(text):
        news = get_news()
        if news:
            messages.insert(0, {
                "role":"system",
                "content":f"Latest Chilean news headline: {news}"
            })
        messages.insert(0, {
            "role": "system",
            "content": VILLAGER_WORLD_PROMPT
        })

    # --- DOLAR ---
    if DOLAR_TRIGGERS.search(text):
        dolar = get_dolar()
        if dolar:
            messages.insert(0, {
                "role":"system",
                "content":f"The current USD to CLP exchange rate is approximately {dolar} CLP."
            })

    payload["model"] = OPENAI_MODEL

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload
    )

    return Response(content=r.content, status_code=r.status_code)

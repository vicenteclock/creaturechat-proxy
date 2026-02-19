import os
import re
import requests
from fastapi import FastAPI, Request, Response

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"

app = FastAPI()

# Ruta raíz para verificar que el proxy está vivo
@app.get("/")
def root():
    return {"status": "proxy alive"}

TRIGGERS = re.compile(r"\b(d[oó]lar|usd|uf|euro|eur)\b", re.IGNORECASE)

def get_dolar():
    try:
        data = requests.get("https://mindicador.cl/api/dolar").json()
        return data["serie"][0]["valor"]
    except:
        return None

@app.post("/v1/chat/completions")
async def chat(req: Request):
    payload = await req.json()
    messages = payload.get("messages", [])

    text = " ".join([m.get("content","") for m in messages if isinstance(m, dict)])

    if TRIGGERS.search(text):
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

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import openai
import requests
from typing import Dict

load_dotenv()

app = FastAPI(title="WhatsApp IA Bot - Pronto Atendimento")

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "meu_verify_token")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

conversations: Dict[str, list] = {}

def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"Erro ao enviar: {response.text}")
    except Exception as e:
        print(f"Exceção: {e}")

def generate_ai_response(user_message: str, user_id: str) -> str:
    if user_id not in conversations:
        conversations[user_id] = []
    
    conversations[user_id].append({"role": "user", "content": user_message})
    
    system_prompt = os.getenv("SYSTEM_PROMPT", "Você é um atendente profissional, amigável e eficiente.")
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}] + conversations[user_id][-10:],
            max_tokens=400,
            temperature=0.7
        )
        ai_reply = response.choices[0].message.content.strip()
        conversations[user_id].append({"role": "assistant", "content": ai_reply})
        return ai_reply
    except Exception as e:
        return "Desculpe, estou com instabilidade agora. Pode repetir?"

@app.get("/webhook")
def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == VERIFY_TOKEN:
        return request.query_params.get("hub.challenge")
    raise HTTPException(403)

@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for message in value.get("messages", []):
                        if message.get("type") == "text":
                            user_message = message["text"]["body"]
                            from_number = message["from"]
                            reply = generate_ai_response(user_message, from_number)
                            send_whatsapp_message(from_number, reply)
        return {"status": "success"}
    except Exception as e:
        print(f"Erro: {e}")
        return {"status": "error"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
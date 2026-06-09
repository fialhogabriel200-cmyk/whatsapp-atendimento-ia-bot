from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import httpx
from openai import OpenAI

load_dotenv()

app = FastAPI()

ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class WhatsAppMessage(BaseModel):
    object: str
    entry: list

@app.get('/webhook')
def verify_webhook(mode: str = None, token: str = None, challenge: str = None):
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return {'hub.challenge': challenge}
    raise HTTPException(403)

@app.post('/webhook')
async def webhook(request: Request):
    data = await request.json()
    # Processar mensagens aqui
    try:
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                message = change['value'].get('messages', [{}])[0]
                if message.get('type') == 'text':
                    text = message['text']['body']
                    from_number = message['from']
                    # Gerar resposta com IA
                    response = generate_ai_response(text)
                    send_whatsapp_message(from_number, response)
    except Exception as e:
        print(e)
    return {'status': 'ok'}

def generate_ai_response(user_message: str) -> str:
    system_prompt = os.getenv('SYSTEM_PROMPT', 'Você é um atendente útil.')
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ]
    )
    return response.choices[0].message.content

def send_whatsapp_message(to: str, text: str):
    url = f'https://graph.facebook.com/v20.0/{PHONE_ID}/messages'
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}
    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {'body': text}
    }
    httpx.post(url, json=payload, headers=headers)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
# WhatsApp Pronto Atendimento com IA

Bot completo em Python com integração WhatsApp Cloud API + IA.

## Como usar
1. Clone este repositório
2. Copie `.env.example` para `.env` e preencha as credenciais
3. `pip install -r requirements.txt`
4. Rode localmente: `uvicorn main:app --reload`
5. Use ngrok para expor o webhook e configure no Meta Developers.

Personalize o `SYSTEM_PROMPT` no `.env` para mudar o tom e regras do bot.
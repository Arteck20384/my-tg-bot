import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

tg_token = os.environ.get("TELEGRAM_TOKEN")
api_key = os.environ.get("GEMINI_API_KEY") 

bot = Bot(token=tg_token)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Привет! Я твой вечный ИИ-помощник. Задавай любой вопрос на русском!")

@dp.message()
async def handle_message(message: types.Message):
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    url = "https://openrouter.ai"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",  # Обязательно для OpenRouter
        "X-Title": "Telegram Bot Assistant"     # Обязательно для OpenRouter
    }
    data = {
        "model": "qwen/qwen-2-7b-instruct:free",
        "messages": [{"role": "user", "content": message.text}]
    }
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post(url, headers=headers, json=data, timeout=15)
        )
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            reply_text = result['choices']['message']['content']
            await message.answer(reply_text)
        elif 'error' in result:
            await message.answer(f"Ошибка от ИИ: {result['error'].get('message', 'Неизвестная ошибка')}")
        else:
            await message.answer("ИИ вернул пустой ответ. Попробуйте еще раз.")
            
    except Exception as e:
        await message.answer("Ошибка связи с сервером ИИ. Попробуйте еще раз.")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


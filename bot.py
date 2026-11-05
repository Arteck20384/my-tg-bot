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
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://render.com",
        "X-Title": "Telegram Bot Assistant"
    }
    data = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": message.text}]
    }
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post(url, headers=headers, json=data, timeout=15)
        )
        
        # Получаем статус-код ответа
        status_code = response.status_code
        result = response.json()
        
        if status_code == 200 and 'choices' in result and len(result['choices']) > 0:
            reply_text = result['choices']['message']['content']
            await message.answer(reply_text)
        else:
            # Если вернулась ошибка, бот пришлет её точную структуру в чат
            error_msg = result.get('error', {}).get('message', 'Неизвестная ошибка сервера')
            await message.answer(f"Технический сбой (Код {status_code}): {error_msg}")
            
    except Exception as e:
        await message.answer(f"Внутреннее исключение бота: {str(e)}")

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

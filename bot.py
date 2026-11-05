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
    
    url = "https://huggingface.co"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": f"<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n{message.text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
        "parameters": {"max_new_tokens": 500, "return_full_text": False}
    }
    
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post(url, headers=headers, json=data, timeout=15)
        )
        
        status_code = response.status_code
        result = response.json()
        
        if status_code == 200 and isinstance(result, list) and len(result) > 0:
            reply_text = result[0].get('generated_text', '').strip()
            await message.answer(reply_text if reply_text else "ИИ вернул пустой текст.")
        else:
            await message.answer(f"Технический сбой сети. Попробуйте еще раз.")
            
    except Exception as e:
        await message.answer(f"Ошибка обработки: {str(e)}")

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

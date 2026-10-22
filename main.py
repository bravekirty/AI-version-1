from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
import os

from gigachat import GigaChat
import gigachat.context
from gigachat.models import Chat as GChat, Messages, MessagesRole
from typing import List

from database import session_maker
from models import User, Chat, Message
from managers import MChat

import logging
logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="ИИ для колледжа",
    description="Первая версия API.",
    version="1.0.0"
)

load_dotenv()

auth_key = os.getenv("AI_KEY")


class ChatRequest(BaseModel):
    user_id: int
    chat_id: int
    message: str



COLLEGE_CONTEXT = """
Ты - ассистент колледжа. Отвечай на вопросы, используя следующие сведения:
- Название колледжа: IT.Москва
- Директор: Горбунов Станислав Игоревич 
- Специальности: 09.02.01 Компьютерные системы и комплексы; 09.02.06 Сетевое и системное администрирование; 09.02.08 Интеллектуальные интегрированные системы; 09.02.08 Интеллектуальные интегрированные системы; 09.02.09 Веб-разработка; 09.02.10 Разработка компьютерных игр, дополненной и виртуальной реальности; 09.02.10 Разработка компьютерных игр, дополненной и виртуальной реальности; 09.02.11 Разработка и управление программным обеспечением; 09.02.11 Разработка и управление программным обеспечением; 09.02.12 Техническая эксплуатация и сопровождение информационных систем; 09.02.12 Техническая эксплуатация и сопровождение информационных систем; 09.02.12 Техническая эксплуатация и сопровождение информационных систем; 09.02.13 Интеграция решений с применением технологий искусственного интеллекта; 09.02.13 Интеграция решений с применением технологий искусственного интеллекта; 09.02.13 Интеграция решений с применением технологий искусственного интеллекта; 10.02.04 Обеспечение информационной безопасности телекоммуникационных систем; 10.02.04 Обеспечение информационной безопасности телекоммуникационных систем; 10.02.05 Обеспечение информационной безопасности автоматизированных систем; 08.02.15 Информационное моделирование в строительстве; 08.02.15 Информационное моделирование в строительстве; 23.01.18 Мастер вертикального транспорта; 23.01.18 Мастер вертикального транспорта; 54.01.20 Графический дизайнер; 54.01.20 Графический дизайнер
Если вопрос не относится к колледжу или ты не знаешь ответа, скажи об этом честно.
"""



@app.post("/chat")
async def chat_with_model(req: ChatRequest):
    chat_id = req.chat_id
    user_id = req.user_id
    message = req.message
    try:
        async with session_maker() as session:
            chat = await MChat.get_or_create(
                session, id=chat_id, first_message=message, user_id=user_id,
            )
            await MChat.add_message(
                session, chat.id, MessagesRole.USER, message,
            )
            gc_history = ([Messages(role=MessagesRole.SYSTEM, content=COLLEGE_CONTEXT)]
                          + await MChat.get_chat_history(session, chat.id))
            
            with GigaChat(
                base_url="https://api.giga.chat/v1",
                credentials=auth_key,
                model="GigaChat-2",
                verify_ssl_certs=False,
            ) as giga:
                response = giga.chat(GChat(messages=gc_history))

            reply = response.choices[0].message.content
            await MChat.add_message(
                session, chat.id, MessagesRole.ASSISTANT, reply,
            )
            await session.commit()
            return {"reply": reply}
    except Exception as e:
        logger.exception("chat_with_model failed")
    raise HTTPException(status_code=500, detail="internal error {e}")




@app.get("/context")
async def get_context():
    return {"context": COLLEGE_CONTEXT}


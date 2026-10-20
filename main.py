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
    chat_id: int
    message: str


@app.post("/chat")
async def chat_with_model(req: ChatRequest):
    chat_id = req.chat_id
    message = req.message
    try:
        async with session_maker() as session:
            chat = await MChat.get_or_create(
                session, id=chat_id, first_message=message, user_id=1,
            )
            await MChat.add_message(
                session, chat.id, MessagesRole.USER, message,
            )

            gc_history = await MChat.get_chat_history(session, chat.id)
            
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



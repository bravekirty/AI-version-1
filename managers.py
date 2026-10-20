from sqlalchemy import select

from models import Chat, Message

from gigachat import Messages


class MChat:
    model = Chat

    @classmethod
    async def get_or_create(cls, session, id, first_message, user_id=1):
        instance = await session.scalar(select(cls.model).where(cls.model.id == id))
        if instance is not None:
            return instance
        
        instance = cls.model(id=id, user_id=user_id, title=first_message[:50])
        session.add(instance)
        await session.flush()
        return instance


    @classmethod
    async def add_message(cls, session, chat_id, role, content):
        instance = Message(role=role, content=content, chat_id=chat_id)
        session.add(instance)
        await session.flush()
        return instance


    @classmethod
    async def get_chat_history(cls, session, chat_id):
        stmt = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.id)
        )
        rows = (await session.scalars(stmt)).all()
        return [Messages(role=m.role, content=m.content) for m in rows]


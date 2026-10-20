from datetime import datetime

from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from gigachat.models import MessagesRole


class Base(DeclarativeBase):
    ...


class BaseMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)


class User(BaseMixin, Base):
    __tablename__ = "users"

    username: Mapped[str]

    chats: Mapped[list["Chat"]] = relationship(back_populates="user")



class Chat(BaseMixin, Base):
    __tablename__ = "chats"

    title: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(back_populates="chats")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="chat",
        lazy="selectin",
        order_by="Message.created_at"
    )



class Message(BaseMixin, Base):
    __tablename__ = "messages"

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"))
    role: Mapped[MessagesRole] = mapped_column(Enum(MessagesRole))
    content: Mapped[str]

    chat: Mapped["Chat"] = relationship(back_populates="messages")



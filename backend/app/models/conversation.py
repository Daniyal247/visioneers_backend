from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    
    # Conversation context
    context = Column(JSON)  # Store conversation context, user preferences, etc.
    intent = Column(String)  # Current user intent (search, purchase, support, etc.)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")

    def __repr__(self):
        return f"<Conversation(id={self.id}, session_id='{self.session_id}', user_id={self.user_id})>"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    
    # Message metadata
    message_type = Column(String)  # text, product_suggestion, order_confirmation, etc.
    meta_info = Column(JSON)  # Store additional data like product IDs, order details, etc.
    
    # AI response data
    model_used = Column(String)  # Which AI model was used
    tokens_used = Column(Integer)  # Token count for billing
    response_time = Column(Float)  # Response time in seconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', conversation_id={self.conversation_id})>" 
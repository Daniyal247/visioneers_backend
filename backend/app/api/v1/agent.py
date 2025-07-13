from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import json
import uuid
import base64
from pydantic import BaseModel

from ...core.database import get_db
from ...core.security import verify_token
from ...services.ai_agent import AIAgent
from ...models import User

router = APIRouter(prefix="/agent", tags=["AI Agent"])

# Initialize AI agent
ai_agent = AIAgent()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

manager = ConnectionManager()

class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: Optional[int] = None

@router.post("/chat")
async def chat_with_agent(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with the AI agent via REST API"""
    try:
        # Generate session ID if not provided
        if not request.session_id:
            session_id = str(uuid.uuid4())
        else:
            session_id = request.session_id
        
        # Process message with AI agent
        response = await ai_agent.process_user_message(
            user_message=request.message,
            user_id=request.user_id or 1,  # Default user ID for demo
            session_id=session_id,
            db=db
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "response": response["content"],
            "metadata": response.get("metadata", {}),
            "intent": response.get("intent", "general"),
            "response_time": response.get("response_time", 0)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time chat with AI agent"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            user_message = message_data.get("message", "")
            user_id = message_data.get("user_id", 1)  # Default user ID for demo
            
            # Process message with AI agent
            response = await ai_agent.process_user_message(
                user_message=user_message,
                user_id=user_id,
                session_id=session_id,
                db=db
            )
            
            # Send response back to client
            await manager.send_personal_message(
                json.dumps({
                    "type": "agent_response",
                    "content": response["content"],
                    "metadata": response.get("metadata", {}),
                    "intent": response.get("intent", "general"),
                    "response_time": response.get("response_time", 0)
                }),
                session_id
            )
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": f"Error processing message: {str(e)}"
            }),
            session_id
        )
        manager.disconnect(session_id)


@router.get("/conversation/{session_id}")
async def get_conversation_history(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get conversation history for a session"""
    from ...models import Conversation, Message
    
    conversation = db.query(Conversation).filter(
        Conversation.session_id == session_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = db.query(Message).filter(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at).all()
    
    return {
        "session_id": session_id,
        "conversation_id": conversation.id,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "metadata": msg.metadata,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.post("/conversation/{session_id}/clear")
async def clear_conversation(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Clear conversation history for a session"""
    from ...models import Conversation, Message
    
    conversation = db.query(Conversation).filter(
        Conversation.session_id == session_id
    ).first()
    
    if conversation:
        # Delete all messages in the conversation
        db.query(Message).filter(Message.conversation_id == conversation.id).delete()
        db.commit()
    
    return {"success": True, "message": "Conversation cleared"}


@router.get("/intent")
async def analyze_intent(
    message: str,
    db: Session = Depends(get_db)
):
    """Analyze user intent from a message"""
    try:
        # Use AI agent to analyze intent
        intent = ai_agent._analyze_intent(message, [])
        
        return {
            "message": message,
            "intent": intent,
            "confidence": 0.8  # Placeholder confidence score
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing intent: {str(e)}")


@router.get("/suggestions")
async def get_suggestions(
    query: str,
    db: Session = Depends(get_db)
):
    """Get product suggestions based on query"""
    try:
        # Extract search criteria from query
        search_criteria = ai_agent._extract_search_criteria(query)
        
        # Search for products
        products = ai_agent.product_service.search_products(db, search_criteria)
        
        suggestions = []
        for product in products[:5]:  # Limit to 5 suggestions
            suggestions.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "brand": product.brand,
                "category": product.category.name if product.category else None
            })
        
        return {
            "query": query,
            "suggestions": suggestions,
            "total_found": len(products)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")


class VoiceMessageRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    session_id: str
    user_id: Optional[int] = None

@router.post("/voice-message")
async def process_buyer_voice_message(
    request: VoiceMessageRequest,
    db: Session = Depends(get_db)
):
    """Process voice message from buyer"""
    try:
        from ...services.image_analysis_service import ImageAnalysisService
        image_analysis = ImageAnalysisService()
        
        # Decode audio data
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Convert speech to text
        text_message = await image_analysis.speech_to_text(audio_bytes)
        
        # Process the text message with AI agent
        response = await ai_agent.process_user_message(
            user_message=text_message,
            user_id=request.user_id or 1,
            session_id=request.session_id,
            db=db
        )
        
        # Convert AI response to speech (optional)
        audio_response = await image_analysis.text_to_speech(response["content"])
        
        return {
            "success": True,
            "original_text": text_message,
            "response": response["content"],
            "audio_response": base64.b64encode(audio_response).decode(),
            "metadata": response.get("metadata", {}),
            "intent": response.get("intent", "general")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice message: {str(e)}") 
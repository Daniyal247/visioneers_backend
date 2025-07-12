from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json
import uuid
import base64
from io import BytesIO

from ...core.database import get_db
from ...services.ai_agent import AIAgent
from ...services.product_service import ProductService
from ...services.image_analysis_service import ImageAnalysisService
from ...models import Product, Category, User, UserRole

router = APIRouter(prefix="/seller", tags=["Seller"])

# Initialize services
ai_agent = AIAgent()
product_service = ProductService()
image_analysis = ImageAnalysisService()

# Pydantic models
class ProductCreateRequest(BaseModel):
    name: str
    description: str
    price: float
    category_id: int
    brand: Optional[str] = None
    model: Optional[str] = None
    condition: str = "new"
    stock_quantity: int = 1
    specifications: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    condition: Optional[str] = None
    stock_quantity: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

class VoiceMessageRequest(BaseModel):
    audio_data: str  # Base64 encoded audio
    session_id: str
    message_type: str = "product_management"  # product_management, general


@router.post("/analyze-image")
async def analyze_product_image(
    image: UploadFile = File(...),
    seller_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Analyze uploaded product image and extract product information"""
    try:
        # Read image data
        image_data = await image.read()
        
        # Analyze image with AI
        product_info = await image_analysis.analyze_product_image(image_data)
        
        # Get suggested category
        suggested_category = await image_analysis.suggest_category(product_info)
        
        return {
            "success": True,
            "suggested_product": {
                "name": product_info.get("name", ""),
                "description": product_info.get("description", ""),
                "suggested_price": product_info.get("suggested_price", 0.0),
                "brand": product_info.get("brand", ""),
                "model": product_info.get("model", ""),
                "specifications": product_info.get("specifications", {}),
                "suggested_category": suggested_category,
                "confidence_score": product_info.get("confidence", 0.0)
            },
            "message": "Product information extracted successfully. You can edit these details before adding to your store."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing image: {str(e)}")


@router.post("/chat")
async def seller_chat_with_agent(
    message: str,
    session_id: str,
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Chat with AI agent for seller assistance"""
    try:
        # Process message with AI agent (seller mode)
        response = await ai_agent.process_seller_message(
            user_message=message,
            user_id=seller_id,
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


@router.post("/voice-message")
async def process_voice_message(
    request: VoiceMessageRequest,
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Process voice message from seller"""
    try:
        # Decode audio data
        audio_data = base64.b64decode(request.audio_data)
        
        # Convert speech to text
        text_message = await image_analysis.speech_to_text(audio_data)
        
        # Process the text message with AI agent
        response = await ai_agent.process_seller_message(
            user_message=text_message,
            user_id=seller_id,
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


@router.post("/products")
async def create_product(
    request: ProductCreateRequest,
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Create a new product (seller)"""
    try:
        # Verify seller role
        seller = db.query(User).filter(User.id == seller_id, User.role == UserRole.SELLER).first()
        if not seller:
            raise HTTPException(status_code=403, detail="Only sellers can create products")
        
        # Create product
        product = Product(
            name=request.name,
            description=request.description,
            price=request.price,
            category_id=request.category_id,
            seller_id=seller_id,
            brand=request.brand,
            model=request.model,
            condition=request.condition,
            stock_quantity=request.stock_quantity,
            specifications=request.specifications,
            tags=request.tags
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return {
            "success": True,
            "message": "Product created successfully",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "category": product.category.name if product.category else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")


@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    request: ProductUpdateRequest,
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Update a product (seller)"""
    try:
        # Verify seller owns the product
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.seller_id == seller_id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found or not owned by seller")
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        return {
            "success": True,
            "message": "Product updated successfully",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "category": product.category.name if product.category else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")


@router.get("/products")
async def get_seller_products(
    seller_id: int,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all products for a seller"""
    try:
        products = product_service.get_products_by_seller(db, seller_id, limit)
        
        return {
            "success": True,
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "stock_quantity": p.stock_quantity,
                    "brand": p.brand,
                    "model": p.model,
                    "condition": p.condition,
                    "category": p.category.name if p.category else None,
                    "is_active": p.is_active,
                    "is_featured": p.is_featured,
                    "created_at": p.created_at.isoformat()
                }
                for p in products
            ],
            "total_found": len(products)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting seller products: {str(e)}")


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Delete a product (seller)"""
    try:
        # Verify seller owns the product
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.seller_id == seller_id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found or not owned by seller")
        
        # Soft delete (mark as inactive)
        product.is_active = False
        db.commit()
        
        return {
            "success": True,
            "message": "Product deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")


@router.post("/products/{product_id}/update-price")
async def update_product_price_voice(
    product_id: int,
    request: VoiceMessageRequest,
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Update product price using voice command"""
    try:
        # Verify seller owns the product
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.seller_id == seller_id
        ).first()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found or not owned by seller")
        
        # Convert speech to text
        audio_data = base64.b64decode(request.audio_data)
        text_message = await image_analysis.speech_to_text(audio_data)
        
        # Extract price from voice command
        new_price = await ai_agent.extract_price_from_voice(text_message)
        
        if new_price:
            product.price = new_price
            db.commit()
            
            return {
                "success": True,
                "message": f"Price updated to ${new_price}",
                "original_text": text_message,
                "new_price": new_price
            }
        else:
            return {
                "success": False,
                "message": "Could not understand the price. Please try again.",
                "original_text": text_message
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating price: {str(e)}")


@router.get("/analytics")
async def get_seller_analytics(
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Get seller analytics and insights"""
    try:
        # Get seller's products
        products = product_service.get_products_by_seller(db, seller_id, 1000)
        
        # Calculate analytics
        total_products = len(products)
        active_products = len([p for p in products if p.is_active])
        featured_products = len([p for p in products if p.is_featured])
        total_value = sum(p.price * p.stock_quantity for p in products)
        
        # Get category distribution
        categories = {}
        for product in products:
            cat_name = product.category.name if product.category else "Uncategorized"
            categories[cat_name] = categories.get(cat_name, 0) + 1
        
        return {
            "success": True,
            "analytics": {
                "total_products": total_products,
                "active_products": active_products,
                "featured_products": featured_products,
                "total_inventory_value": total_value,
                "category_distribution": categories,
                "average_price": total_value / total_products if total_products > 0 else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analytics: {str(e)}") 
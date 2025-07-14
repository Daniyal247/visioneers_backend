import openai
import json
import time
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from ..core.config import settings
from ..models import User, Product, Conversation, Message, UserRole
from .product_service import ProductService


class AIAgent:
    def __init__(self):
        # Configure OpenAI client for Azure or standard OpenAI
        if settings.openai_api_base and settings.openai_deployment_name:
            # Azure OpenAI configuration
            self.client = openai.AzureOpenAI(
                api_key=settings.openai_api_key,
                api_version=settings.openai_api_version,
                azure_endpoint=settings.openai_api_base
            )
            self.deployment_name = settings.openai_deployment_name
        else:
            # Standard OpenAI configuration
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.deployment_name = None
        
        self.product_service = ProductService()
        
        # System prompt for the AI agent
        self.system_prompt = """You are an AI shopping assistant for Visioneers Marketplace. Your role is to help users find products, make recommendations, and assist with purchases through natural language interactions.

Key capabilities:
1. Product Search: Help users find specific products based on their needs
2. Recommendations: Suggest products based on user preferences and browsing history
3. Product Information: Provide detailed information about products
4. Purchase Assistance: Help users complete purchases
5. Support: Answer questions about orders, shipping, returns, etc.

IMPORTANT: Always maintain conversation context. Remember previous user preferences, search criteria, and product discussions. When users refer to products mentioned earlier, use that context to provide relevant responses.

Always be helpful, friendly, and professional. When suggesting products, provide relevant details like price, features, and availability. If you don't have information about a specific product, say so and suggest alternatives."""

    async def process_user_message(
        self, 
        user_message: str, 
        user_id: int, 
        session_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Process a user message and generate an AI response"""
        
        start_time = time.time()
        
        # Get or create conversation
        conversation = self._get_or_create_conversation(db, user_id, session_id)
        
        # Get conversation history
        conversation_history = self._get_conversation_history(db, conversation.id)
        
        # Analyze user intent
        intent = self._analyze_intent(user_message, conversation_history)
        
        # Generate response based on intent
        if intent == "product_search":
            response = await self._handle_product_search(user_message, db, conversation_history)
        elif intent == "product_info":
            response = await self._handle_product_info(user_message, db, conversation_history)
        elif intent == "purchase":
            response = await self._handle_purchase(user_message, db, conversation_history)
        elif intent == "recommendation":
            response = await self._handle_recommendation(user_message, db, conversation_history)
        else:
            response = await self._handle_general_query(user_message, conversation_history)
        
        # Save messages to database
        self._save_message(db, conversation.id, "user", user_message)
        self._save_message(db, conversation.id, "assistant", response["content"], response.get("metadata"))
        
        # Calculate response time
        response_time = time.time() - start_time
        
        return {
            "content": response["content"],
            "metadata": response.get("metadata", {}),
            "intent": intent,
            "response_time": response_time
        }

    def _get_or_create_conversation(self, db: Session, user_id: int, session_id: str) -> Conversation:
        """Get existing conversation or create new one"""
        # First, ensure the user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # Create a default user if it doesn't exist
            user = User(
                id=user_id,
                email=f"user{user_id}@example.com",
                username=f"user{user_id}",
                hashed_password="default_password_hash",
                full_name=f"User {user_id}",
                role=UserRole.BUYER
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        conversation = db.query(Conversation).filter(
            Conversation.session_id == session_id,
            Conversation.is_active == True
        ).first()
        
        if not conversation:
            conversation = Conversation(
                user_id=user_id,
                session_id=session_id,
                context={},
                intent="general"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        return conversation

    def _get_conversation_history(self, db: Session, conversation_id: int) -> List[Dict]:
        """Get conversation history for context"""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).limit(settings.max_conversation_history).all()
        
        return [
            {"role": msg.role, "content": msg.content}
            for msg in reversed(messages)
        ]

    def _analyze_intent(self, user_message: str, conversation_history: List[Dict]) -> str:
        """Analyze user intent from message"""
        prompt = f"""Analyze the user's intent from this message: "{user_message}"

Previous conversation context:
{json.dumps(conversation_history[-3:], indent=2)}

Classify the intent as one of:
- product_search: User is looking for products
- product_info: User wants information about a specific product
- purchase: User wants to buy something
- recommendation: User wants recommendations
- general: General question or support

Respond with just the intent category."""

        try:
            # Use deployment name for Azure, model name for standard OpenAI
            model_or_deployment = self.deployment_name if self.deployment_name else "gpt-3.5-turbo"
            
            response = self.client.chat.completions.create(
                model=model_or_deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            return response.choices[0].message.content.strip().lower()
        except Exception:
            return "general"

    async def _handle_product_search(self, user_message: str, db: Session, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle product search requests"""
        # Extract search criteria from user message
        search_criteria = self._extract_search_criteria(user_message)
        
        # Search for products
        products = self.product_service.search_products(db, search_criteria)
        
        if not products:
            return {
                "content": "I couldn't find any products matching your criteria. Could you please provide more details about what you're looking for?",
                "metadata": {"products": []}
            }
        
        # Format product suggestions with complete information
        product_suggestions = []
        for product in products[:5]:  # Limit to 5 suggestions
            product_suggestions.append({
                "id": product.id,
                "name": product.name,
                "price": product.price,
                "description": product.description,
                "brand": product.brand,
                "model": product.model,
                "condition": product.condition,
                "stock_quantity": product.stock_quantity,
                "category": product.category.name if product.category else None,
                "seller_id": product.seller_id,
                "images": product.images,
                "specifications": product.specifications,
                "tags": product.tags,
                "is_active": product.is_active,
                "is_featured": product.is_featured
            })
        
        response_text = "Here are some products that match your search:\n\n"
        for i, product in enumerate(product_suggestions, 1):
            response_text += f"{i}. **{product['name']}** - ${product['price']}\n"
            response_text += f"   Brand: {product['brand']}\n"
            response_text += f"   {product['description']}\n\n"
        
        response_text += "Would you like me to show you more details about any of these products?"
        
        return {
            "content": response_text,
            "metadata": {"products": product_suggestions, "search_criteria": search_criteria}
        }

    async def _handle_product_info(self, user_message: str, db: Session, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle requests for specific product information"""
        # Extract product identifier from message
        product_identifier = self._extract_product_identifier(user_message)
        
        if not product_identifier:
            return {
                "content": "I couldn't identify which product you're asking about. Could you please specify the product name or ID?",
                "metadata": {}
            }
        
        # Find the product
        product = self.product_service.get_product_by_identifier(db, product_identifier)
        
        if not product:
            return {
                "content": f"I couldn't find a product matching '{product_identifier}'. Could you please check the product name or try a different search?",
                "metadata": {}
            }
        
        # Format detailed product information
        response_text = f"**{product.name}**\n\n"
        response_text += f"**Price:** ${product.price}\n"
        response_text += f"**Brand:** {product.brand}\n"
        response_text += f"**Category:** {product.category.name if product.category else 'N/A'}\n"
        response_text += f"**Condition:** {product.condition}\n"
        response_text += f"**Stock:** {product.stock_quantity} available\n\n"
        response_text += f"**Description:**\n{product.description}\n\n"
        
        if product.specifications:
            response_text += "**Specifications:**\n"
            for key, value in product.specifications.items():
                response_text += f"- {key}: {value}\n"
        
        response_text += f"\nWould you like to purchase this product or see similar items?"
        
        return {
            "content": response_text,
            "metadata": {
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "price": product.price,
                    "brand": product.brand,
                    "stock_quantity": product.stock_quantity
                }
            }
        }

    async def _handle_purchase(self, user_message: str, db: Session, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle purchase requests"""
        # Extract product and quantity information
        purchase_info = self._extract_purchase_info(user_message)
        
        if not purchase_info:
            return {
                "content": "I couldn't understand your purchase request. Could you please specify which product you'd like to buy and the quantity?",
                "metadata": {}
            }
        
        # Check product availability
        product = self.product_service.get_product_by_id(db, purchase_info["product_id"])
        
        if not product:
            return {
                "content": "I couldn't find the product you're trying to purchase. Please check the product ID or name.",
                "metadata": {}
            }
        
        if product.stock_quantity < purchase_info["quantity"]:
            return {
                "content": f"Sorry, only {product.stock_quantity} units of {product.name} are available. Would you like to purchase the available quantity?",
                "metadata": {"available_quantity": product.stock_quantity}
            }
        
        # Calculate total
        total = product.price * purchase_info["quantity"]
        
        response_text = f"Great! Here's your order summary:\n\n"
        response_text += f"**Product:** {product.name}\n"
        response_text += f"**Quantity:** {purchase_info['quantity']}\n"
        response_text += f"**Price per unit:** ${product.price}\n"
        response_text += f"**Total:** ${total}\n\n"
        response_text += "Would you like to proceed with the purchase? I can help you complete the checkout process."
        
        return {
            "content": response_text,
            "metadata": {
                "purchase_info": {
                    "product_id": product.id,
                    "quantity": purchase_info["quantity"],
                    "unit_price": product.price,
                    "total": total
                }
            }
        }

    async def _handle_recommendation(self, user_message: str, db: Session, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle recommendation requests"""
        # Extract user preferences from message and conversation history
        preferences = self._extract_preferences(user_message, conversation_history)
        
        # Get recommendations
        recommendations = self.product_service.get_recommendations(db, preferences)
        
        if not recommendations:
            return {
                "content": "I couldn't find any recommendations based on your preferences. Could you tell me more about what you're looking for?",
                "metadata": {"recommendations": []}
            }
        
        response_text = "Based on your preferences, here are some recommendations:\n\n"
        for i, product in enumerate(recommendations[:5], 1):
            response_text += f"{i}. **{product.name}** - ${product.price}\n"
            response_text += f"   {product.description[:100]}...\n\n"
        
        return {
            "content": response_text,
            "metadata": {"recommendations": [{"id": p.id, "name": p.name, "price": p.price} for p in recommendations]}
        }

    async def _handle_general_query(self, user_message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle general queries using AI with enhanced context awareness"""
        # Build context-aware prompt
        context_summary = ""
        if conversation_history:
            recent_messages = conversation_history[-3:]  # Last 3 messages for context
            context_summary = f"\n\nRecent conversation context:\n"
            for msg in recent_messages:
                context_summary += f"- {msg['role']}: {msg['content'][:100]}...\n"
        
        enhanced_prompt = self.system_prompt + context_summary + "\n\nCurrent user message: " + user_message
        
        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=settings.agent_model,
                messages=messages,
                max_tokens=500,
                temperature=settings.agent_temperature
            )
            
            return {
                "content": response.choices[0].message.content,
                "metadata": {}
            }
        except Exception as e:
            return {
                "content": "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment.",
                "metadata": {"error": str(e)}
            }

    def _extract_search_criteria(self, message: str) -> Dict[str, Any]:
        """Extract search criteria from user message"""
        # This is a simplified version - in production, you'd use more sophisticated NLP
        criteria = {}
        
        # Extract price range
        if "under" in message.lower() or "less than" in message.lower():
            # Simple price extraction - in production, use regex or NLP
            criteria["max_price"] = 100  # Default value
        
        # Extract category
        categories = ["electronics", "clothing", "books", "home", "sports"]
        for category in categories:
            if category in message.lower():
                criteria["category"] = category
                break
        
        # Extract brand
        brands = ["apple", "samsung", "nike", "adidas", "sony"]
        for brand in brands:
            if brand in message.lower():
                criteria["brand"] = brand
                break
        
        return criteria

    def _extract_product_identifier(self, message: str) -> Optional[str]:
        """Extract product identifier from message"""
        # Simple extraction - in production, use more sophisticated NLP
        words = message.lower().split()
        # Look for product names or IDs
        return None  # Simplified for now

    def _extract_purchase_info(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract purchase information from message"""
        # Simplified extraction
        return None  # Simplified for now

    def _extract_preferences(self, message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Extract user preferences from message and conversation history"""
        preferences = {}
        
        # Analyze message for preferences
        if "cheap" in message.lower() or "budget" in message.lower():
            preferences["price_range"] = "low"
        elif "premium" in message.lower() or "high-end" in message.lower():
            preferences["price_range"] = "high"
        
        return preferences

    def _save_message(self, db: Session, conversation_id: int, role: str, content: str, metadata: Optional[Dict] = None):
        """Save message to database"""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            role=role,
            meta_info=metadata or {},
            model_used=settings.agent_model
        )
        db.add(message)
        db.commit()

    async def process_seller_message(
        self, 
        user_message: str, 
        user_id: int, 
        session_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Process a seller message and generate an AI response"""
        
        start_time = time.time()
        
        # Get or create conversation
        conversation = self._get_or_create_conversation(db, user_id, session_id)
        
        # Get conversation history
        conversation_history = self._get_conversation_history(db, conversation.id)
        
        # Analyze seller intent
        intent = self._analyze_seller_intent(user_message, conversation_history)
        
        # Generate response based on intent
        if intent == "product_management":
            response = await self._handle_product_management(user_message, db, conversation_history)
        elif intent == "pricing":
            response = await self._handle_pricing_help(user_message, db, conversation_history)
        elif intent == "analytics":
            response = await self._handle_analytics_request(user_message, db, conversation_history)
        elif intent == "inventory":
            response = await self._handle_inventory_management(user_message, db, conversation_history)
        else:
            response = await self._handle_general_seller_query(user_message, conversation_history)
        
        # Save messages to database
        self._save_message(db, conversation.id, "user", user_message)
        self._save_message(db, conversation.id, "assistant", response["content"], response.get("metadata"))
        
        # Calculate response time
        response_time = time.time() - start_time
        
        return {
            "content": response["content"],
            "metadata": response.get("metadata", {}),
            "intent": intent,
            "response_time": response_time
        }

    def _analyze_seller_intent(self, user_message: str, conversation_history: List[Dict]) -> str:
        """Analyze seller intent from message"""
        prompt = f"""Analyze the seller's intent from this message: "{user_message}"

Previous conversation context:
{json.dumps(conversation_history[-3:], indent=2)}

Classify the intent as one of:
- product_management: Managing products (add, edit, delete)
- pricing: Price-related questions or changes
- analytics: Sales analytics, performance questions
- inventory: Stock management, inventory questions
- general: General seller support

Respond with just the intent category."""

        try:
            # Use deployment name for Azure, model name for standard OpenAI
            model_or_deployment = self.deployment_name if self.deployment_name else "gpt-3.5-turbo"
            
            response = self.client.chat.completions.create(
                model=model_or_deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            return response.choices[0].message.content.strip().lower()
        except Exception:
            return "general"

    async def _handle_product_management(self, user_message: str, db: Session, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle product management requests"""
        response_text = "I can help you manage your products! Here's what I can do:\n\n"
        response_text += "• **Add Products**: Upload an image and I'll extract product info\n"
        response_text += "• **Edit Products**: Change names, descriptions, prices, etc.\n"
        response_text += "• **Delete Products**: Remove products from your store\n"
        response_text += "• **Bulk Operations**: Manage multiple products at once\n\n"
        response_text += "Just tell me what you'd like to do, or upload a product image to get started!"
        
        return {
            "content": response_text,
            "metadata": {"capabilities": ["add", "edit", "delete", "bulk"]}
        }

    async def _handle_pricing_help(self, user_message: str, db: Session, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle pricing-related requests"""
        response_text = "I can help you with pricing strategies!\n\n"
        response_text += "• **Market Research**: I can search current market prices\n"
        response_text += "• **Price Optimization**: Suggest optimal pricing based on competition\n"
        response_text += "• **Dynamic Pricing**: Adjust prices based on demand\n"
        response_text += "• **Price Updates**: Change prices via voice or text\n\n"
        response_text += "What pricing help do you need?"
        
        return {
            "content": response_text,
            "metadata": {"pricing_features": ["market_research", "optimization", "dynamic", "updates"]}
        }

    async def _handle_analytics_request(self, user_message: str, db: Session, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle analytics requests"""
        response_text = "Here are your store analytics insights:\n\n"
        response_text += "• **Sales Performance**: Track revenue and growth\n"
        response_text += "• **Product Performance**: See which products sell best\n"
        response_text += "• **Customer Insights**: Understand buyer behavior\n"
        response_text += "• **Inventory Analytics**: Monitor stock levels and turnover\n\n"
        response_text += "I can provide detailed reports and recommendations!"
        
        return {
            "content": response_text,
            "metadata": {"analytics_types": ["sales", "products", "customers", "inventory"]}
        }

    async def _handle_inventory_management(self, user_message: str, db: Session, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle inventory management requests"""
        response_text = "I can help you manage your inventory!\n\n"
        response_text += "• **Stock Updates**: Update quantities via voice or text\n"
        response_text += "• **Low Stock Alerts**: Get notified when items run low\n"
        response_text += "• **Inventory Reports**: Track stock levels and movement\n"
        response_text += "• **Restock Suggestions**: Get recommendations for reordering\n\n"
        response_text += "What inventory help do you need?"
        
        return {
            "content": response_text,
            "metadata": {"inventory_features": ["updates", "alerts", "reports", "restock"]}
        }

    async def _handle_general_seller_query(self, user_message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Handle general seller queries"""
        seller_system_prompt = """You are an AI assistant for marketplace sellers. Help them with:

1. Product Management: Adding, editing, deleting products
2. Pricing Strategy: Market research, price optimization
3. Inventory Management: Stock updates, restock alerts
4. Analytics: Sales reports, performance insights
5. Store Optimization: SEO, marketing, customer service

Be helpful, professional, and provide actionable advice."""
        
        messages = [
            {"role": "system", "content": seller_system_prompt},
            *conversation_history[-5:],
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=settings.agent_model,
                messages=messages,
                max_tokens=500,
                temperature=settings.agent_temperature
            )
            
            return {
                "content": response.choices[0].message.content,
                "metadata": {}
            }
        except Exception as e:
            return {
                "content": "I'm sorry, I'm having trouble processing your request right now. Please try again in a moment.",
                "metadata": {"error": str(e)}
            }

    async def extract_price_from_voice(self, text_message: str) -> Optional[float]:
        """Extract price from voice command"""
        try:
            prompt = f"""Extract the price from this voice command: "{text_message}"

            Look for:
            - Dollar amounts (e.g., "fifty dollars" = $50.00)
            - Numbers followed by "dollars" or "$"
            - Price ranges (take the first mentioned price)
            
            Return only the numeric price value, or null if no price found."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            price_text = response.choices[0].message.content.strip()
            
            # Try to convert to float
            try:
                return float(price_text)
            except ValueError:
                return None
                
        except Exception:
            return None

    async def extract_product_updates_from_voice(self, text_message: str, product) -> Optional[Dict[str, Any]]:
        """Extract product updates from voice command"""
        prompt = f"""Extract product updates from this voice command: "{text_message}"

Current product info:
- Name: {product.name}
- Price: ${product.price}
- Description: {product.description}
- Condition: {product.condition}
- Stock: {product.stock_quantity}

Look for updates to:
- name: Product name changes
- price: Price changes (numeric values)
- description: Description updates
- condition: Condition changes (new, used, refurbished)
- stock_quantity: Stock quantity changes (numeric values)
- brand: Brand changes
- model: Model changes

Return a JSON object with only the fields that need to be updated, or null if no valid updates found.

Examples:
- "Change the price to $99.99" → {{"price": 99.99}}
- "Update the name to iPhone 15 Pro" → {{"name": "iPhone 15 Pro"}}
- "Set description to latest model" → {{"description": "latest model"}}
- "Change condition to used" → {{"condition": "used"}}
- "Update stock to 25 units" → {{"stock_quantity": 25}}
- "Change brand to Apple" → {{"brand": "Apple"}}

Return only the JSON object, no additional text."""

        try:
            model_or_deployment = self.deployment_name if self.deployment_name else "gpt-3.5-turbo"
            
            response = self.client.chat.completions.create(
                model=model_or_deployment,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            # Try to parse as JSON
            try:
                import json
                updates = json.loads(result)
                
                # Validate that updates contain valid fields
                valid_fields = ['name', 'price', 'description', 'condition', 'stock_quantity', 'brand', 'model']
                filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}
                
                return filtered_updates if filtered_updates else None
                
            except json.JSONDecodeError:
                return None
                
        except Exception:
            return None 
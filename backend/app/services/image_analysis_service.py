import openai
import base64
import io
from PIL import Image
import requests
from typing import Dict, Any, Optional
from ..core.config import settings

class ImageAnalysisService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def analyze_product_image(self, image_data: bytes) -> Dict[str, Any]:
        """Analyze product image and extract information using AI"""
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create prompt for product analysis
            prompt = """Analyze this product image and extract the following information:
            
            - Product name
            - Brand
            - Model (if applicable)
            - Suggested price (based on market research)
            - Product description
            - Key specifications/features
            - Product condition (new, used, refurbished)
            
            Return the information in JSON format with these fields:
            {
                "name": "Product Name",
                "brand": "Brand Name",
                "model": "Model Number",
                "suggested_price": 0.0,
                "description": "Product description",
                "specifications": {
                    "key1": "value1",
                    "key2": "value2"
                },
                "condition": "new/used/refurbished",
                "confidence": 0.85
            }
            
            Be accurate and realistic with pricing. If you can't identify the product clearly, indicate low confidence."""
            
            # Use OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                import json
                # Find JSON in the response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    product_info = json.loads(json_str)
                else:
                    # Fallback: create basic info
                    product_info = {
                        "name": "Product",
                        "brand": "Unknown",
                        "model": "",
                        "suggested_price": 0.0,
                        "description": content,
                        "specifications": {},
                        "condition": "new",
                        "confidence": 0.5
                    }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                product_info = {
                    "name": "Product",
                    "brand": "Unknown",
                    "model": "",
                    "suggested_price": 0.0,
                    "description": content,
                    "specifications": {},
                    "condition": "new",
                    "confidence": 0.3
                }
            
            return product_info
            
        except Exception as e:
            # Return default info on error
            return {
                "name": "Product",
                "brand": "Unknown",
                "model": "",
                "suggested_price": 0.0,
                "description": "Product information could not be extracted automatically.",
                "specifications": {},
                "condition": "new",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def suggest_category(self, product_info: Dict[str, Any]) -> str:
        """Suggest product category based on extracted information"""
        try:
            # Create prompt for category suggestion
            prompt = f"""Based on this product information, suggest the most appropriate category:

            Product: {product_info.get('name', 'Unknown')}
            Brand: {product_info.get('brand', 'Unknown')}
            Description: {product_info.get('description', '')}
            
            Choose from these categories:
            - Electronics
            - Clothing & Fashion
            - Home & Garden
            - Sports & Outdoors
            - Books & Media
            - Automotive
            - Health & Beauty
            - Toys & Games
            - Food & Beverages
            - Other
            
            Respond with just the category name."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=20,
                temperature=0.1
            )
            
            category = response.choices[0].message.content.strip()
            return category
            
        except Exception as e:
            return "Other"
    
    async def speech_to_text(self, audio_data: bytes) -> str:
        """Convert speech to text using OpenAI Whisper"""
        try:
            # Create a file-like object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"  # Give it a filename
            
            # Use OpenAI Whisper API
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
            
            return response
            
        except Exception as e:
            return f"Error converting speech to text: {str(e)}"
    
    async def text_to_speech(self, text: str) -> bytes:
        """Convert text to speech using OpenAI TTS"""
        try:
            # Use OpenAI TTS API
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Get the audio data
            audio_data = response.content
            return audio_data
            
        except Exception as e:
            # Return empty audio on error
            return b""
    
    async def search_web_for_product_info(self, product_name: str, brand: str = "") -> Dict[str, Any]:
        """Search web for additional product information"""
        try:
            search_query = f"{brand} {product_name}" if brand else product_name
            
            prompt = f"""Search for information about this product: {search_query}
            
            Find:
            - Current market price
            - Key specifications
            - Popular features
            - User reviews summary
            
            Return in JSON format:
            {{
                "market_price": 0.0,
                "specifications": {{}},
                "features": [],
                "review_summary": "string"
            }}"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Try to parse JSON
            try:
                import json
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    return json.loads(json_str)
                else:
                    return {
                        "market_price": 0.0,
                        "specifications": {},
                        "features": [],
                        "review_summary": content
                    }
            except json.JSONDecodeError:
                return {
                    "market_price": 0.0,
                    "specifications": {},
                    "features": [],
                    "review_summary": content
                }
                
        except Exception as e:
            return {
                "market_price": 0.0,
                "specifications": {},
                "features": [],
                "review_summary": f"Error searching web: {str(e)}"
            }
    
    async def validate_product_info(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and improve extracted product information"""
        try:
            prompt = f"""Validate and improve this product information:

            Current Info:
            {product_info}
            
            Please:
            1. Validate the price is reasonable
            2. Improve the description if needed
            3. Add missing specifications
            4. Suggest better product name if unclear
            
            Return improved info in JSON format."""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
            # Try to parse JSON
            try:
                import json
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    return json.loads(json_str)
                else:
                    return product_info
            except json.JSONDecodeError:
                return product_info
                
        except Exception as e:
            return product_info 
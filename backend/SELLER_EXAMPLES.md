# AI-Powered Seller System Examples

## 🎯 **How It Works**

The seller system is **completely AI-driven** - sellers can manage their entire store through natural language and voice commands!

## 📸 **1. Image Analysis & Product Extraction**

### **Upload Product Image**
```bash
curl -X POST "http://localhost:8000/api/v1/seller/analyze-image" \
  -H "Content-Type: multipart/form-data" \
  -F "image=@laptop_photo.jpg" \
  -F "seller_id=1"
```

**Response:**
```json
{
  "success": true,
  "suggested_product": {
    "name": "ASUS ROG Strix G15 Gaming Laptop",
    "description": "High-performance gaming laptop with RTX 3060 graphics",
    "suggested_price": 1299.99,
    "brand": "ASUS",
    "model": "G15",
    "specifications": {
      "processor": "AMD Ryzen 7 5800H",
      "graphics": "NVIDIA RTX 3060 6GB",
      "ram": "16GB DDR4",
      "storage": "512GB NVMe SSD",
      "display": "15.6\" 144Hz Full HD"
    },
    "suggested_category": "Electronics",
    "confidence_score": 0.92
  },
  "message": "Product information extracted successfully. You can edit these details before adding to your store."
}
```

## 🗣️ **2. Voice Commands for Product Management**

### **Voice: "Change the price to $1,199"**
```bash
curl -X POST "http://localhost:8000/api/v1/seller/products/123/update-price" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64_encoded_audio_data",
    "session_id": "seller-session-123",
    "message_type": "product_management"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Price updated to $1,199",
  "original_text": "Change the price to $1,199",
  "new_price": 1199.0
}
```

### **Voice: "Add 5 more units to stock"**
```bash
curl -X POST "http://localhost:8000/api/v1/seller/voice-message" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64_encoded_audio_data",
    "session_id": "seller-session-123",
    "message_type": "product_management"
  }'
```

**Response:**
```json
{
  "success": true,
  "original_text": "Add 5 more units to stock",
  "response": "I've updated the stock quantity for your ASUS laptop. Added 5 more units. Current stock is now 15 units.",
  "audio_response": "base64_encoded_audio_response",
  "metadata": {
    "product_id": 123,
    "stock_change": 5,
    "new_stock": 15
  },
  "intent": "inventory"
}
```

## 💬 **3. Text Chat with AI Agent**

### **Seller: "Help me optimize my pricing"**
```bash
curl -X POST "http://localhost:8000/api/v1/seller/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Help me optimize my pricing",
    "session_id": "seller-session-123",
    "seller_id": 1
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "I can help you with pricing strategies!\n\n• **Market Research**: I can search current market prices\n• **Price Optimization**: Suggest optimal pricing based on competition\n• **Dynamic Pricing**: Adjust prices based on demand\n• **Price Updates**: Change prices via voice or text\n\nWhat pricing help do you need?",
  "metadata": {
    "pricing_features": ["market_research", "optimization", "dynamic", "updates"]
  },
  "intent": "pricing"
}
```

### **Seller: "Show me my sales analytics"**
```bash
curl -X POST "http://localhost:8000/api/v1/seller/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Show me my sales analytics",
    "session_id": "seller-session-123",
    "seller_id": 1
  }'
```

**Response:**
```json
{
  "success": true,
  "response": "Here are your store analytics insights:\n\n• **Sales Performance**: Track revenue and growth\n• **Product Performance**: See which products sell best\n• **Customer Insights**: Understand buyer behavior\n• **Inventory Analytics**: Monitor stock levels and turnover\n\nI can provide detailed reports and recommendations!",
  "metadata": {
    "analytics_types": ["sales", "products", "customers", "inventory"]
  },
  "intent": "analytics"
}
```

## 🛍️ **4. Buyer Voice Commands**

### **Buyer: "I need a gaming laptop under $1500"**
```bash
curl -X POST "http://localhost:8000/api/v1/agent/voice-message" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "base64_encoded_audio_data",
    "session_id": "buyer-session-123",
    "user_id": 1
  }'
```

**Response:**
```json
{
  "success": true,
  "original_text": "I need a gaming laptop under $1500",
  "response": "Here are some excellent gaming laptops under $1500:\n\n1. **ASUS ROG Strix G15** - $1,299\n   RTX 3060, 16GB RAM, 512GB SSD\n\n2. **Lenovo Legion 5** - $1,199\n   RTX 3050, 8GB RAM, 256GB SSD\n\nWhich one interests you?",
  "audio_response": "base64_encoded_audio_response",
  "metadata": {
    "products": [
      {
        "id": 123,
        "name": "ASUS ROG Strix G15",
        "price": 1299.0,
        "brand": "ASUS"
      }
    ]
  },
  "intent": "product_search"
}
```

## 🔧 **5. Complete Seller Workflow**

### **Step 1: Upload Product Image**
```javascript
// Frontend code
const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('seller_id', sellerId);
  
  const response = await fetch('/api/v1/seller/analyze-image', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  // Show suggested product details for editing
  displayProductForm(data.suggested_product);
};
```

### **Step 2: Edit via Voice**
```javascript
// Voice editing
const editProductVoice = async (audioBlob) => {
  const base64Audio = await blobToBase64(audioBlob);
  
  const response = await fetch('/api/v1/seller/voice-message', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      audio_data: base64Audio,
      session_id: sessionId,
      message_type: 'product_management'
    })
  });
  
  const data = await response.json();
  // Update UI with changes
  updateProductDetails(data.metadata);
};
```

### **Step 3: Create Product**
```javascript
// Create product with AI-suggested details
const createProduct = async (productData) => {
  const response = await fetch('/api/v1/seller/products', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: productData.name,
      description: productData.description,
      price: productData.suggested_price,
      category_id: productData.category_id,
      brand: productData.brand,
      specifications: productData.specifications
    })
  });
  
  const data = await response.json();
  // Product created successfully
};
```

## 🎯 **6. Advanced AI Features**

### **Market Research**
```
Seller: "What's the current market price for gaming laptops?"
AI: "Based on my research, gaming laptops with RTX 3060 are currently priced between $1,100-$1,400. Your ASUS ROG at $1,299 is competitively priced. Consider highlighting the 144Hz display and 16GB RAM as unique selling points."
```

### **Inventory Management**
```
Seller: "I'm running low on the ASUS laptop"
AI: "I've checked your inventory. You have 3 units left of the ASUS ROG Strix G15. Would you like me to:
1. Order more stock (estimated delivery: 5-7 days)
2. Increase the price due to limited availability
3. Mark it as 'limited stock' to create urgency"
```

### **Pricing Optimization**
```
Seller: "Should I lower my prices?"
AI: "Looking at your sales data and market trends:
• Your ASUS laptop is priced 5% below market average
• It's your best-selling product
• Current stock turnover is healthy
• Recommendation: Keep current pricing, but consider a 10% discount for bulk purchases to increase volume."
```

## 🚀 **7. Frontend Integration**

### **React Seller Dashboard**
```javascript
const SellerDashboard = () => {
  const [products, setProducts] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  
  // Voice recording
  const startVoiceCommand = async () => {
    setIsRecording(true);
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.ondataavailable = async (event) => {
      const audioBlob = event.data;
      const base64Audio = await blobToBase64(audioBlob);
      
      const response = await fetch('/api/v1/seller/voice-message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          audio_data: base64Audio,
          session_id: sessionId,
          message_type: 'product_management'
        })
      });
      
      const data = await response.json();
      // Handle AI response
      handleAIResponse(data);
    };
    
    mediaRecorder.start();
  };
  
  return (
    <div className="seller-dashboard">
      <div className="voice-controls">
        <button onClick={startVoiceCommand}>
          {isRecording ? 'Recording...' : '🎤 Voice Command'}
        </button>
      </div>
      
      <div className="product-upload">
        <input type="file" accept="image/*" onChange={uploadImage} />
        <p>Upload product image for AI analysis</p>
      </div>
      
      <div className="ai-chat">
        <input 
          type="text" 
          placeholder="Ask AI for help..."
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              sendMessage(e.target.value);
            }
          }}
        />
      </div>
    </div>
  );
};
```

## 🎯 **Key Benefits**

1. **Zero Learning Curve**: Sellers can use natural language
2. **Voice-First**: Hands-free product management
3. **AI-Powered**: Automatic product info extraction
4. **Smart Suggestions**: Market research and pricing advice
5. **Real-time Analytics**: Instant insights and recommendations

This creates a **revolutionary seller experience** where managing an online store becomes as simple as having a conversation with an AI assistant! 
# Visioneers Marketplace Backend

An AI-powered marketplace backend with an intelligent shopping assistant that helps users find products, make recommendations, and complete purchases through natural language interactions.

## Features

- **AI Shopping Assistant**: Conversational AI agent that understands user intent and provides personalized product recommendations
- **Product Search & Filtering**: Advanced search capabilities with multiple criteria
- **Real-time Chat**: WebSocket support for real-time conversations with the AI agent
- **User Management**: Authentication and user role management (buyer/seller/admin)
- **Order Management**: Complete order processing and tracking
- **Conversation History**: Persistent chat history for context-aware interactions

## Architecture

```
visioneers_marketplace/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration, database, security
│   │   ├── models/         # Database models
│   │   ├── api/v1/         # API endpoints
│   │   ├── services/       # Business logic (AI agent, product service)
│   │   └── main.py         # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── env.example        # Environment variables template
```

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI**: OpenAI GPT-4 for natural language processing
- **Real-time**: WebSocket support for live chat
- **Authentication**: JWT tokens
- **Caching**: Redis (optional)

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (optional, for caching)

### 2. Environment Setup

1. Clone the repository
2. Navigate to the backend directory
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Copy environment template:
   ```bash
   cp env.example .env
   ```

6. Configure environment variables in `.env`:
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/visioneers_marketplace
   
   # AI Provider
   OPENAI_API_KEY=your-openai-api-key
   
   # Security
   SECRET_KEY=your-secret-key-here
   ```

### 3. Database Setup

1. Create PostgreSQL database:
   ```sql
   CREATE DATABASE visioneers_marketplace;
   ```

2. Run database migrations (tables will be created automatically on startup)

### 4. Run the Application

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python -m app.main
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## AI Agent API Endpoints

### Chat with AI Agent

**POST** `/api/v1/agent/chat`
```json
{
  "message": "I'm looking for a laptop under $1000",
  "session_id": "user-session-123",
  "user_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "user-session-123",
  "response": "Here are some laptops under $1000:\n\n1. **Dell Inspiron 15** - $899\n   Brand: Dell\n   Intel i5 processor, 8GB RAM, 256GB SSD\n\n2. **HP Pavilion** - $799\n   Brand: HP\n   AMD Ryzen 5, 8GB RAM, 512GB SSD\n\nWould you like me to show you more details about any of these products?",
  "metadata": {
    "products": [
      {
        "id": 1,
        "name": "Dell Inspiron 15",
        "price": 899.0,
        "brand": "Dell",
        "category": "Electronics"
      }
    ],
    "search_criteria": {
      "max_price": 1000,
      "category": "electronics"
    }
  },
  "intent": "product_search",
  "response_time": 1.2
}
```

### WebSocket Chat

**WebSocket** `/api/v1/agent/ws/{session_id}`

Send messages via WebSocket for real-time chat:
```json
{
  "message": "Show me the details of the Dell laptop",
  "user_id": 1
}
```

### Get Conversation History

**GET** `/api/v1/agent/conversation/{session_id}`

### Clear Conversation

**POST** `/api/v1/agent/conversation/{session_id}/clear`

### Analyze Intent

**GET** `/api/v1/agent/intent?message=I want to buy a phone`

### Get Product Suggestions

**GET** `/api/v1/agent/suggestions?query=laptop`

## AI Agent Capabilities

### 1. Product Search
- Natural language product queries
- Price range filtering
- Category-based search
- Brand-specific searches

### 2. Product Information
- Detailed product specifications
- Pricing and availability
- Related products

### 3. Purchase Assistance
- Order summary generation
- Stock availability checking
- Checkout process guidance

### 4. Recommendations
- Personalized product suggestions
- Based on user preferences and history
- Trending and featured products

### 5. General Support
- Order tracking
- Return policies
- Shipping information
- General marketplace questions

## Example Conversations

### Product Search
```
User: "I need a gaming laptop for under $1500"
Agent: "Here are some great gaming laptops under $1500:\n\n1. **ASUS ROG Strix** - $1,299\n   RTX 3060, 16GB RAM, 512GB SSD\n\n2. **Lenovo Legion 5** - $1,199\n   RTX 3050, 8GB RAM, 256GB SSD\n\nWhich one interests you?"
```

### Product Details
```
User: "Tell me more about the ASUS ROG"
Agent: "**ASUS ROG Strix G15**\n\n**Price:** $1,299\n**Brand:** ASUS\n**Category:** Gaming Laptops\n**Specifications:**\n- NVIDIA RTX 3060 6GB\n- AMD Ryzen 7 5800H\n- 16GB DDR4 RAM\n- 512GB NVMe SSD\n- 15.6" 144Hz Display\n\n**Stock:** 5 available\n\nWould you like to purchase this laptop?"
```

### Purchase Process
```
User: "Yes, I want to buy it"
Agent: "Great! Here's your order summary:\n\n**Product:** ASUS ROG Strix G15\n**Quantity:** 1\n**Price per unit:** $1,299\n**Total:** $1,299\n\nWould you like to proceed with the purchase? I can help you complete the checkout process."
```

## Development

### Adding New Features

1. **New AI Capabilities**: Extend the `AIAgent` class in `services/ai_agent.py`
2. **New API Endpoints**: Add routes in `api/v1/` directory
3. **Database Models**: Create models in `models/` directory
4. **Business Logic**: Implement services in `services/` directory

### Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

## Production Deployment

### Environment Variables
- Set `DEBUG=False`
- Configure production database
- Set secure `SECRET_KEY`
- Configure CORS origins
- Set up proper logging

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Scaling Considerations
- Use Redis for session management
- Implement database connection pooling
- Add rate limiting
- Set up monitoring and logging
- Use CDN for static assets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 
# Visioneers Marketplace Backend

An AI-powered marketplace backend with an intelligent shopping assistant that helps users find products, make recommendations, and complete purchases through natural language interactions.

## Features

- **AI Shopping Assistant**: Conversational AI agent that understands user intent and provides personalized product recommendations
- **Product Search & Filtering**: Advanced search capabilities with multiple criteria
- **Real-time Chat**: WebSocket support for real-time conversations with the AI agent
- **User Management**: Authentication and user role management (buyer/seller/admin)
- **Order Management**: Complete order processing and tracking
- **Conversation History**: Persistent chat history for context-aware interactions
- **Email Verification**: N8N integration for user registration confirmation emails

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
│   ├── debug_shell         # To read or get the data from the DB about the users
│   ├── requirements.txt    # Python dependencies
│   └── env.example        # Environment variables template
```

Also adding n8n in the Solution to send confirmation mailing when someone signs up.

## Database Schema

The Visioneers Marketplace uses PostgreSQL with the following schema:

### Core Tables

#### 1. Users Table (`users`)
```sql
- id (Primary Key, Integer)
- email (Unique, indexed, String)
- username (Unique, indexed, String)
- hashed_password (String)
- full_name (String)
- role (Enum: BUYER, SELLER, ADMIN)
- is_active (Boolean, default: true)
- is_verified (Boolean, default: false)
- created_at (Timestamp)
- updated_at (Timestamp)
- email_verification_token (String, nullable)
- email_token_expires_at (Timestamp, nullable)
```

#### 2. Categories Table (`categories`)
```sql
- id (Primary Key, Integer)
- name (Unique, indexed, String)
- description (Text)
- parent_id (Foreign Key → categories.id, nullable)
- created_at (Timestamp)
```

#### 3. Products Table (`products`)
```sql
- id (Primary Key, Integer)
- name (Indexed, String)
- description (Text)
- price (Float)
- stock_quantity (Integer, default: 0)
- category_id (Foreign Key → categories.id)
- seller_id (Foreign Key → users.id)
- brand (String)
- model (String)
- condition (String: new, used, refurbished)
- specifications (JSON)
- images (JSON array of URLs)
- tags (JSON array)
- is_active (Boolean, default: true)
- is_featured (Boolean, default: false)
- created_at (Timestamp)
- updated_at (Timestamp)
```

#### 4. Orders Table (`orders`)
```sql
- id (Primary Key, Integer)
- order_number (Unique, indexed, String)
- buyer_id (Foreign Key → users.id)
- total_amount (Float)
- shipping_address (String)
- billing_address (String)
- order_status (Enum: PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED, REFUNDED)
- payment_status (Enum: PENDING, PAID, FAILED, REFUNDED)
- payment_method (String)
- payment_transaction_id (String)
- created_at (Timestamp)
- updated_at (Timestamp)
```

#### 5. Order Items Table (`order_items`)
```sql
- id (Primary Key, Integer)
- order_id (Foreign Key → orders.id)
- product_id (Foreign Key → products.id)
- quantity (Integer)
- unit_price (Float)
- total_price (Float)
- created_at (Timestamp)
```

#### 6. Conversations Table (`conversations`)
```sql
- id (Primary Key, Integer)
- user_id (Foreign Key → users.id)
- session_id (Unique, indexed, String)
- context (JSON)
- intent (String)
- is_active (Boolean, default: true)
- created_at (Timestamp)
- updated_at (Timestamp)
```

#### 7. Messages Table (`messages`)
```sql
- id (Primary Key, Integer)
- conversation_id (Foreign Key → conversations.id)
- content (Text)
- role (String: user, assistant, system)
- message_type (String)
- meta_info (JSON)
- model_used (String)
- tokens_used (Integer)
- response_time (Float)
- created_at (Timestamp)
```

### Database Relationships

```
Users (1) ←→ (Many) Products (as seller)
Users (1) ←→ (Many) Orders (as buyer)
Users (1) ←→ (Many) Conversations

Categories (1) ←→ (Many) Products
Categories (1) ←→ (Many) Categories (self-referencing for hierarchy)

Orders (1) ←→ (Many) OrderItems
Products (1) ←→ (Many) OrderItems

Conversations (1) ←→ (Many) Messages
```

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI**: OpenAI GPT-4 for natural language processing
- **Real-time**: WebSocket support for live chat
- **Authentication**: JWT tokens
- **Caching**: Redis (optional)
- **Email Integration**: N8N for automated email verification

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
   DATABASE_URL=postgresql://visioneers_user:visioneers_password@visioneers_postgres_dev:5432/visioneers_marketplace_dev
   
   # AI Provider
   OPENAI_API_KEY=your-openai-api-key
   OPENAI_API_BASE=Your-openai-base-url
   OPENAI_API_VERSION=your-model-version
   OPENAI_DEPLOYMENT_NAME=your-deployment-name
   
   # Security
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

### 3. Database Setup

1. Create PostgreSQL database:
   ```sql
   CREATE DATABASE visioneers_marketplace_dev;
   ```

2. Run database setup:
   ```bash
   python setup_database.py
   ```

3. Add missing columns (if needed):
   ```bash
   python add_missing_columns.py
   ```

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

## API Endpoints

### Authentication (`/api/v1/auth`)

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "password123",
  "full_name": "John Doe",
  "role": "buyer"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

#### Verify Email
```http
GET /api/v1/auth/verify/{token}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer {access_token}
```

### Products (`/api/v1/products`)

#### Get All Products
```http
GET /api/v1/products
```

#### Get Product by ID
```http
GET /api/v1/products/{product_id}
```

#### Create Product (Seller only)
```http
POST /api/v1/products
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "Product Name",
  "description": "Product description",
  "price": 99.99,
  "category_id": 1,
  "stock_quantity": 10
}
```

### Seller Dashboard (`/api/v1/seller`)

#### Get Seller Products
```http
GET /api/v1/seller/products
Authorization: Bearer {access_token}
```

#### Update Product
```http
PUT /api/v1/seller/products/{product_id}
Authorization: Bearer {access_token}
```

## Email Verification Flow

### Registration Process

1. **User registers** via `/api/v1/auth/register`
2. **System creates user** with verification token
3. **N8N webhook called** with email and token
4. **Email sent** with verification link
5. **User clicks link** → `/api/v1/auth/verify/{token}`
6. **User verified** and can login

### N8N Integration

The system integrates with N8N for email verification:

**Webhook URL**: `https://dani127.app.n8n.cloud/webhook/send-verification`

**Payload**:
```json
{
  "email": "user@example.com",
  "token": "abc123def456..."
}
```

**Expected N8N Flow**:
1. Receive webhook with email and token
2. Generate verification link: `http://your-frontend.com/verify?token={token}`
3. Send email with verification link
4. User clicks link and gets verified

### Verification Endpoint

```http
GET /api/v1/auth/verify/{token}
```

**Response**:
```json
{
  "success": true,
  "message": "Email verified successfully! You can now log in."
}
```

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
# Visioneers Marketplace - Docker Setup Guide

This guide covers how to run the Visioneers Marketplace backend using Docker and Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Email Verification Flow](#email-verification-flow)
6. [Environment Configuration](#environment-configuration)
7. [Docker Commands](#docker-commands)
8. [Database Management](#database-management)
9. [Troubleshooting](#troubleshooting)
10. [Production Deployment](#production-deployment)

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- At least 4GB of available RAM
- At least 10GB of available disk space

## Quick Start

### 1. Clone and Setup

```bash
# Navigate to the backend directory
cd backend

# Copy environment file
cp env.example .env

# Edit .env file with your configuration
# Make sure to set your OpenAI API key
```

### 2. Development Environment

```bash
# Start development environment with hot reload
docker-compose -f docker-compose.dev.yml up --build

# Or start in background
docker-compose -f docker-compose.dev.yml up -d --build
```

**Development Features:**
- Hot reload enabled
- pgAdmin available at http://localhost:5050
- Redis Commander available at http://localhost:8081
- API available at http://localhost:8000
- API docs at http://localhost:8000/docs

### 3. Production Environment

```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up --build

# Or start in background
docker-compose -f docker-compose.prod.yml up -d --build
```

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

### Database Setup

```bash
# Create database tables
docker exec -it visioneers_backend_dev python setup_database.py

# Add missing columns (if needed)
docker exec -it visioneers_backend_dev python add_missing_columns.py
```

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

### AI Agent (`/api/v1/agent`)

#### Chat with AI
```http
POST /api/v1/agent/chat
Content-Type: application/json

{
  "message": "Hello, I'm looking for electronics",
  "session_id": "unique-session-id"
}
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

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://visioneers_user:visioneers_password@visioneers_postgres_dev:5432/visioneers_marketplace_dev
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_BASE=https://kaispeazureai.openai.azure.com/
OPENAI_API_VERSION=2024-02-15-preview
OPENAI_DEPLOYMENT_NAME=gpt-4o

# Application Settings
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Production Settings
POSTGRES_USER=visioneers_user
POSTGRES_PASSWORD=visioneers_password
```

## Docker Commands

### Development

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Start with rebuild
docker-compose -f docker-compose.dev.yml up --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop development environment
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes
docker-compose -f docker-compose.dev.yml down -v
```

### Production

```bash
# Start production environment
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop production environment
docker-compose -f docker-compose.prod.yml down

# Update and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Individual Services

```bash
# Start only database
docker-compose up postgres redis

# Start only backend
docker-compose up backend

# Rebuild specific service
docker-compose build backend

# View service logs
docker-compose logs backend
```

## Database Management

### Access PostgreSQL

```bash
# Connect to PostgreSQL container
docker exec -it visioneers_postgres_dev psql -U visioneers_user -d visioneers_marketplace_dev

# Or using docker-compose
docker-compose exec postgres psql -U visioneers_user -d visioneers_marketplace_dev
```

### pgAdmin (Development)

1. Open http://localhost:5050
2. Login with:
   - Email: admin@visioneers.com
   - Password: admin123
3. Add server:
   - Host: postgres
   - Port: 5432
   - Database: visioneers_marketplace_dev
   - Username: visioneers_user
   - Password: visioneers_password

### Redis Management

```bash
# Connect to Redis
docker exec -it visioneers_redis redis-cli

# Or using docker-compose
docker-compose exec redis redis-cli
```

### Redis Commander (Development)

1. Open http://localhost:8081
2. View Redis data in web interface

## File Structure

```
backend/
├── Dockerfile                 # Production Docker image
├── Dockerfile.dev            # Development Docker image
├── docker-compose.yml        # Main compose file
├── docker-compose.dev.yml    # Development compose file
├── docker-compose.prod.yml   # Production compose file
├── .dockerignore             # Files to exclude from build
├── nginx.conf               # Nginx reverse proxy config
├── init.sql                 # Database initialization
├── backup.sh                # Database backup script
├── env.example              # Environment variables template
├── uploads/                 # File uploads (mounted volume)
├── logs/                    # Application logs (mounted volume)
├── app/
│   ├── api/v1/             # API endpoints
│   ├── core/               # Core configuration
│   ├── models/             # Database models
│   └── services/           # Business logic
└── setup_database.py       # Database setup script
```

## Health Checks

The application includes health checks for all services:

- **Backend**: `http://localhost:8000/health`
- **PostgreSQL**: Database connectivity
- **Redis**: Connection ping

## Monitoring

### View Container Status

```bash
# All containers
docker ps

# Specific compose project
docker-compose ps
```

### Resource Usage

```bash
# Container resource usage
docker stats

# Specific container
docker stats visioneers_backend
```

### Logs

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs backend
```

## Backup and Restore

### Automated Backups (Production)

```bash
# Run backup manually
docker-compose -f docker-compose.prod.yml run backup

# Or schedule with cron
0 2 * * * docker-compose -f /path/to/docker-compose.prod.yml run backup
```

### Manual Backup

```bash
# Create backup
docker exec visioneers_postgres_dev pg_dump -U visioneers_user visioneers_marketplace_dev > backup.sql

# Restore backup
docker exec -i visioneers_postgres_dev psql -U visioneers_user visioneers_marketplace_dev < backup.sql
```

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the port
   netstat -tulpn | grep :8000
   
   # Change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use different host port
   ```

2. **Permission issues**
   ```bash
   # Fix upload directory permissions
   sudo chown -R 1000:1000 uploads/
   ```

3. **Database connection issues**
   ```bash
   # Check database logs
   docker-compose logs postgres
   
   # Restart database
   docker-compose restart postgres
   ```

4. **Memory issues**
   ```bash
   # Check available memory
   docker system df
   
   # Clean up unused resources
   docker system prune
   ```

5. **Missing database columns**
   ```bash
   # Add missing columns
   docker exec -it visioneers_backend_dev python add_missing_columns.py
   ```

### Debugging

```bash
# Access container shell
docker exec -it visioneers_backend bash

# View application logs
docker logs visioneers_backend

# Check environment variables
docker exec visioneers_backend env
```

## Production Deployment

### Environment Setup

1. Set production environment variables
2. Configure SSL certificates
3. Set up monitoring and logging
4. Configure backup strategy

### Security Considerations

- Change default passwords
- Use strong SECRET_KEY
- Enable SSL/TLS
- Configure firewall rules
- Regular security updates

### Scaling

```bash
# Scale backend service
docker-compose -f docker-compose.prod.yml up --scale backend=3

# Use external load balancer
# Configure nginx for load balancing
```

## Performance Optimization

### Database

```bash
# Optimize PostgreSQL
docker-compose exec postgres psql -U visioneers_user -d visioneers_marketplace_dev -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
"
```

### Redis

```bash
# Optimize Redis
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## API Testing

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs

# Test chat endpoint
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-session"}'

# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "password123", "full_name": "Test User"}'
```

## Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Verify environment variables
3. Check container health: `docker ps`
4. Review this documentation

## Next Steps

1. Set up CI/CD pipeline
2. Configure monitoring (Prometheus, Grafana)
3. Set up logging aggregation
4. Implement automated testing
5. Configure production SSL certificates 
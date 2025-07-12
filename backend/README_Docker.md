# Visioneers Marketplace - Docker Setup Guide

This guide covers how to run the Visioneers Marketplace backend using Docker and Docker Compose.

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

## Environment Configuration

### Required Environment Variables

Create a `.env` file in the backend directory:

```bash
# Database Configuration
DATABASE_URL=postgresql://visioneers_user:visioneers_password@postgres:5432/visioneers_marketplace
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Application Settings
DEBUG=False
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
docker exec -it visioneers_postgres psql -U visioneers_user -d visioneers_marketplace

# Or using docker-compose
docker-compose exec postgres psql -U visioneers_user -d visioneers_marketplace
```

### pgAdmin (Development)

1. Open http://localhost:5050
2. Login with:
   - Email: admin@visioneers.com
   - Password: admin123
3. Add server:
   - Host: postgres
   - Port: 5432
   - Database: visioneers_marketplace
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
└── logs/                    # Application logs (mounted volume)
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
docker exec visioneers_postgres pg_dump -U visioneers_user visioneers_marketplace > backup.sql

# Restore backup
docker exec -i visioneers_postgres psql -U visioneers_user visioneers_marketplace < backup.sql
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
docker-compose exec postgres psql -U visioneers_user -d visioneers_marketplace -c "
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
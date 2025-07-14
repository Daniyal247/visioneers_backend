from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn
from sqlalchemy.orm import Session

from .core.config import settings
from .core.database import engine, Base, SessionLocal
from .models import Category, Product, User, UserRole
from .api.v1 import agent, products, seller, auth

# Create database tables and initialize data
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    
    # Initialize default categories and sample data if they don't exist
    db = SessionLocal()
    try:
        # Check if categories exist
        existing_categories = db.query(Category).count()
        if existing_categories == 0:
            # Create default categories
            default_categories = [
                Category(name="Electronics", description="Electronic devices and gadgets"),
                Category(name="Clothing", description="Apparel and fashion items"),
                Category(name="Home & Garden", description="Home improvement and garden supplies"),
                Category(name="Sports & Outdoors", description="Sports equipment and outdoor gear"),
                Category(name="Books & Media", description="Books, movies, and digital media"),
                Category(name="Automotive", description="Car parts and accessories"),
                Category(name="Health & Beauty", description="Health products and beauty supplies"),
                Category(name="Toys & Games", description="Toys, games, and entertainment"),
                Category(name="Jewelry & Watches", description="Jewelry and timepieces"),
                Category(name="Collectibles", description="Collectible items and memorabilia")
            ]
            
            for category in default_categories:
                db.add(category)
            
            db.commit()
            print("✅ Default categories created successfully")
        else:
            print(f"✅ Found {existing_categories} existing categories")
        
        # Check if sample products exist
        existing_products = db.query(Product).count()
        if existing_products == 0:
            # Get category IDs
            electronics_category = db.query(Category).filter(Category.name == "Electronics").first()
            clothing_category = db.query(Category).filter(Category.name == "Clothing").first()
            
            # Create sample seller
            sample_seller = User(
                email="seller@example.com",
                username="sample_seller",
                hashed_password="hashed_password",
                full_name="Sample Seller",
                role=UserRole.SELLER
            )
            db.add(sample_seller)
            db.commit()
            db.refresh(sample_seller)
            
            # Create sample products
            sample_products = [
                Product(
                    name="Vintage Adidas Gazelle - Blue",
                    description="Authentic vintage Adidas Gazelle sneakers in classic blue colorway. Excellent condition with minimal wear. Perfect for collectors or casual wear.",
                    price=85.00,
                    category_id=clothing_category.id if clothing_category else 1,
                    seller_id=sample_seller.id,
                    brand="Adidas",
                    model="Gazelle",
                    condition="Very Good",
                    stock_quantity=3,
                    specifications={
                        "size": "US 10",
                        "material": "Leather",
                        "year": "1990s",
                        "color": "Blue"
                    },
                    tags=["vintage", "sneakers", "adidas", "classic"],
                    images=[
                        "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop",
                        "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=400&h=400&fit=crop"
                    ],
                    is_active=True,
                    is_featured=True
                ),
                Product(
                    name="Classic Vans Old Skool - Black",
                    description="Timeless Vans Old Skool sneakers in black. Great condition with original box. Perfect everyday sneakers.",
                    price=65.00,
                    category_id=clothing_category.id if clothing_category else 1,
                    seller_id=sample_seller.id,
                    brand="Vans",
                    model="Old Skool",
                    condition="Good",
                    stock_quantity=5,
                    specifications={
                        "size": "US 9",
                        "material": "Canvas",
                        "color": "Black",
                        "style": "Classic"
                    },
                    tags=["vans", "sneakers", "classic", "black"],
                    images=[
                        "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=400&h=400&fit=crop",
                        "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=400&h=400&fit=crop"
                    ],
                    is_active=True,
                    is_featured=False
                ),
                Product(
                    name="Retro Converse Chuck 70",
                    description="Authentic vintage Converse Chuck Taylor 70s in excellent condition. Rare colorway with original details.",
                    price=78.00,
                    category_id=clothing_category.id if clothing_category else 1,
                    seller_id=sample_seller.id,
                    brand="Converse",
                    model="Chuck 70",
                    condition="Excellent",
                    stock_quantity=2,
                    specifications={
                        "size": "US 8",
                        "material": "Canvas",
                        "year": "1980s",
                        "color": "White/Red"
                    },
                    tags=["converse", "vintage", "chuck", "rare"],
                    images=[
                        "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=400&h=400&fit=crop",
                        "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=400&fit=crop"
                    ],
                    is_active=True,
                    is_featured=True
                ),
                Product(
                    name="ASUS ROG Strix Gaming Laptop",
                    description="High-performance gaming laptop with RTX 3060 graphics, perfect for gaming and content creation.",
                    price=1299.99,
                    category_id=electronics_category.id if electronics_category else 1,
                    seller_id=sample_seller.id,
                    brand="ASUS",
                    model="ROG Strix G15",
                    condition="New",
                    stock_quantity=4,
                    specifications={
                        "processor": "AMD Ryzen 7 5800H",
                        "graphics": "NVIDIA RTX 3060 6GB",
                        "ram": "16GB DDR4",
                        "storage": "512GB NVMe SSD",
                        "display": "15.6\" 144Hz Full HD"
                    },
                    tags=["gaming", "laptop", "asus", "rtx"],
                    images=[
                        "https://images.unsplash.com/photo-1603302576837-37561b2e2302?w=400&h=400&fit=crop",
                        "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?w=400&h=400&fit=crop"
                    ],
                    is_active=True,
                    is_featured=True
                ),
                Product(
                    name="iPhone 13 Pro - 128GB",
                    description="Excellent condition iPhone 13 Pro with 128GB storage. Includes original box and accessories.",
                    price=799.99,
                    category_id=electronics_category.id if electronics_category else 1,
                    seller_id=sample_seller.id,
                    brand="Apple",
                    model="iPhone 13 Pro",
                    condition="Excellent",
                    stock_quantity=2,
                    specifications={
                        "storage": "128GB",
                        "color": "Sierra Blue",
                        "condition": "Excellent",
                        "includes": "Box, charger, cable"
                    },
                    tags=["iphone", "apple", "smartphone", "pro"],
                    images=[
                        "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?w=400&h=400&fit=crop",
                        "https://images.unsplash.com/photo-1592899677977-9c5ca4d4c1b4?w=400&h=400&fit=crop"
                    ],
                    is_active=True,
                    is_featured=False
                )
            ]
            
            for product in sample_products:
                db.add(product)
            
            db.commit()
            print("✅ Sample products created successfully")
        else:
            print(f"✅ Found {existing_products} existing products")
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
    
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title="Visioneers Marketplace API",
    description="AI-powered marketplace backend with intelligent shopping assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

# Include routers
app.include_router(agent.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(seller.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Visioneers Marketplace API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={"error": "Not found", "detail": "The requested resource was not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 
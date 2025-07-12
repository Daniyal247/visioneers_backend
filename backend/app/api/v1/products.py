from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ...core.database import get_db
from ...services.product_service import ProductService
from ...models import Product, Category

router = APIRouter(prefix="/products", tags=["Products"])

# Initialize product service
product_service = ProductService()

# Pydantic models for request/response
class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    brand: Optional[str] = None
    model: Optional[str] = None
    condition: Optional[str] = None
    category: Optional[str] = None
    seller: Optional[str] = None
    is_featured: bool
    images: Optional[List[str]] = None
    specifications: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    condition: Optional[str] = None
    in_stock_only: bool = True
    sort_by: str = "featured"  # featured, price_low, price_high, newest, name
    limit: int = 20
    offset: int = 0


@router.get("/search")
async def search_products(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Category filter"),
    brand: Optional[str] = Query(None, description="Brand filter"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    condition: Optional[str] = Query(None, description="Product condition"),
    in_stock_only: bool = Query(True, description="Show only in-stock items"),
    sort_by: str = Query("featured", description="Sort by: featured, price_low, price_high, newest, name"),
    limit: int = Query(20, description="Number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Search products with filters"""
    try:
        search_params = {
            "search_text": query,
            "category": category,
            "brand": brand,
            "min_price": min_price,
            "max_price": max_price,
            "condition": condition,
            "in_stock_only": in_stock_only,
            "sort_by": sort_by,
            "limit": limit,
            "offset": offset
        }
        
        products = product_service.search_products_advanced(db, search_params)
        
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
                    "seller": p.seller.username if p.seller else None,
                    "is_featured": p.is_featured,
                    "images": p.images,
                    "specifications": p.specifications
                }
                for p in products
            ],
            "total_found": len(products),
            "search_params": search_params
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")


@router.get("/")
async def get_products(
    limit: int = Query(20, description="Number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    featured_only: bool = Query(False, description="Show only featured products"),
    db: Session = Depends(get_db)
):
    """Get all products with pagination"""
    try:
        if featured_only:
            products = product_service.get_featured_products(db, limit)
        else:
            # Get all active products
            products = db.query(Product).filter(
                Product.is_active == True
            ).order_by(Product.created_at.desc()).offset(offset).limit(limit).all()
        
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
                    "seller": p.seller.username if p.seller else None,
                    "is_featured": p.is_featured,
                    "images": p.images,
                    "specifications": p.specifications
                }
                for p in products
            ],
            "total_found": len(products)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting products: {str(e)}")


@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get product by ID"""
    try:
        product = product_service.get_product_by_id(db, product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "brand": product.brand,
                "model": product.model,
                "condition": product.condition,
                "category": product.category.name if product.category else None,
                "seller": product.seller.username if product.seller else None,
                "is_featured": product.is_featured,
                "images": product.images,
                "specifications": product.specifications,
                "tags": product.tags,
                "created_at": product.created_at.isoformat(),
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting product: {str(e)}")


@router.get("/category/{category_name}")
async def get_products_by_category(
    category_name: str,
    limit: int = Query(20, description="Number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get products by category"""
    try:
        products = product_service.get_products_by_category(db, category_name, limit)
        
        return {
            "success": True,
            "category": category_name,
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
                    "seller": p.seller.username if p.seller else None,
                    "is_featured": p.is_featured,
                    "images": p.images,
                    "specifications": p.specifications
                }
                for p in products
            ],
            "total_found": len(products)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting products by category: {str(e)}")


@router.get("/brand/{brand_name}")
async def get_products_by_brand(
    brand_name: str,
    limit: int = Query(20, description="Number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """Get products by brand"""
    try:
        products = db.query(Product).filter(
            Product.brand.ilike(f"%{brand_name}%"),
            Product.is_active == True
        ).order_by(Product.price).offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "brand": brand_name,
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
                    "seller": p.seller.username if p.seller else None,
                    "is_featured": p.is_featured,
                    "images": p.images,
                    "specifications": p.specifications
                }
                for p in products
            ],
            "total_found": len(products)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting products by brand: {str(e)}")


@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    try:
        categories = product_service.get_categories(db)
        
        return {
            "success": True,
            "categories": [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "parent_id": c.parent_id
                }
                for c in categories
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")


@router.get("/featured")
async def get_featured_products(
    limit: int = Query(10, description="Number of featured products"),
    db: Session = Depends(get_db)
):
    """Get featured products"""
    try:
        products = product_service.get_featured_products(db, limit)
        
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
                    "seller": p.seller.username if p.seller else None,
                    "is_featured": p.is_featured,
                    "images": p.images,
                    "specifications": p.specifications
                }
                for p in products
            ],
            "total_found": len(products)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting featured products: {str(e)}") 
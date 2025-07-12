from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from ..models import Product, Category, User


class ProductService:
    def __init__(self):
        pass

    def search_products(self, db: Session, criteria: Dict[str, Any]) -> List[Product]:
        """Search products based on criteria"""
        query = db.query(Product).filter(Product.is_active == True)
        
        # Apply filters based on criteria
        if criteria.get("category"):
            query = query.join(Category).filter(Category.name.ilike(f"%{criteria['category']}%"))
        
        if criteria.get("brand"):
            query = query.filter(Product.brand.ilike(f"%{criteria['brand']}%"))
        
        if criteria.get("max_price"):
            query = query.filter(Product.price <= criteria["max_price"])
        
        if criteria.get("min_price"):
            query = query.filter(Product.price >= criteria["min_price"])
        
        if criteria.get("keyword"):
            keyword = criteria["keyword"]
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{keyword}%"),
                    Product.description.ilike(f"%{keyword}%"),
                    Product.brand.ilike(f"%{keyword}%")
                )
            )
        
        # Filter by stock availability
        if criteria.get("in_stock_only", True):
            query = query.filter(Product.stock_quantity > 0)
        
        # Order by relevance (featured first, then by price or name)
        query = query.order_by(desc(Product.is_featured), Product.price)
        
        return query.limit(20).all()

    def get_product_by_id(self, db: Session, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        return db.query(Product).filter(Product.id == product_id).first()

    def get_product_by_identifier(self, db: Session, identifier: str) -> Optional[Product]:
        """Get product by name, ID, or other identifier"""
        # Try to find by ID first
        try:
            product_id = int(identifier)
            product = self.get_product_by_id(db, product_id)
            if product:
                return product
        except ValueError:
            pass
        
        # Try to find by name
        return db.query(Product).filter(
            and_(
                Product.name.ilike(f"%{identifier}%"),
                Product.is_active == True
            )
        ).first()

    def get_recommendations(self, db: Session, preferences: Dict[str, Any]) -> List[Product]:
        """Get product recommendations based on user preferences"""
        query = db.query(Product).filter(Product.is_active == True)
        
        # Apply preference filters
        if preferences.get("price_range") == "low":
            query = query.filter(Product.price <= 50)
        elif preferences.get("price_range") == "high":
            query = query.filter(Product.price >= 200)
        
        if preferences.get("category"):
            query = query.join(Category).filter(Category.name.ilike(f"%{preferences['category']}%"))
        
        if preferences.get("brand"):
            query = query.filter(Product.brand.ilike(f"%{preferences['brand']}%"))
        
        # Filter by stock
        query = query.filter(Product.stock_quantity > 0)
        
        # Order by featured products first, then by price
        query = query.order_by(desc(Product.is_featured), Product.price)
        
        return query.limit(10).all()

    def get_featured_products(self, db: Session, limit: int = 10) -> List[Product]:
        """Get featured products"""
        return db.query(Product).filter(
            and_(
                Product.is_active == True,
                Product.is_featured == True,
                Product.stock_quantity > 0
            )
        ).order_by(Product.price).limit(limit).all()

    def get_products_by_category(self, db: Session, category_name: str, limit: int = 20) -> List[Product]:
        """Get products by category"""
        return db.query(Product).join(Category).filter(
            and_(
                Category.name.ilike(f"%{category_name}%"),
                Product.is_active == True,
                Product.stock_quantity > 0
            )
        ).order_by(desc(Product.is_featured), Product.price).limit(limit).all()

    def get_products_by_seller(self, db: Session, seller_id: int, limit: int = 20) -> List[Product]:
        """Get products by seller"""
        return db.query(Product).filter(
            and_(
                Product.seller_id == seller_id,
                Product.is_active == True
            )
        ).order_by(desc(Product.created_at)).limit(limit).all()

    def update_stock(self, db: Session, product_id: int, quantity: int) -> bool:
        """Update product stock quantity"""
        product = self.get_product_by_id(db, product_id)
        if product and product.stock_quantity >= quantity:
            product.stock_quantity -= quantity
            db.commit()
            return True
        return False

    def search_products_advanced(self, db: Session, search_params: Dict[str, Any]) -> List[Product]:
        """Advanced product search with multiple criteria"""
        query = db.query(Product).filter(Product.is_active == True)
        
        # Text search
        if search_params.get("search_text"):
            search_text = search_params["search_text"]
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search_text}%"),
                    Product.description.ilike(f"%{search_text}%"),
                    Product.brand.ilike(f"%{search_text}%"),
                    Product.model.ilike(f"%{search_text}%")
                )
            )
        
        # Price range
        if search_params.get("min_price"):
            query = query.filter(Product.price >= search_params["min_price"])
        if search_params.get("max_price"):
            query = query.filter(Product.price <= search_params["max_price"])
        
        # Category
        if search_params.get("category_id"):
            query = query.filter(Product.category_id == search_params["category_id"])
        
        # Brand
        if search_params.get("brand"):
            query = query.filter(Product.brand.ilike(f"%{search_params['brand']}%"))
        
        # Condition
        if search_params.get("condition"):
            query = query.filter(Product.condition == search_params["condition"])
        
        # Stock availability
        if search_params.get("in_stock_only", True):
            query = query.filter(Product.stock_quantity > 0)
        
        # Seller
        if search_params.get("seller_id"):
            query = query.filter(Product.seller_id == search_params["seller_id"])
        
        # Sort options
        sort_by = search_params.get("sort_by", "featured")
        if sort_by == "price_low":
            query = query.order_by(Product.price)
        elif sort_by == "price_high":
            query = query.order_by(desc(Product.price))
        elif sort_by == "newest":
            query = query.order_by(desc(Product.created_at))
        elif sort_by == "name":
            query = query.order_by(Product.name)
        else:  # featured
            query = query.order_by(desc(Product.is_featured), Product.price)
        
        # Pagination
        limit = search_params.get("limit", 20)
        offset = search_params.get("offset", 0)
        
        return query.offset(offset).limit(limit).all()

    def get_categories(self, db: Session) -> List[Category]:
        """Get all categories"""
        return db.query(Category).all()

    def get_category_by_name(self, db: Session, name: str) -> Optional[Category]:
        """Get category by name"""
        return db.query(Category).filter(Category.name.ilike(f"%{name}%")).first() 
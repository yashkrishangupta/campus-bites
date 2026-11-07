from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database import Base


# Food Shops Table
class FoodShop(Base):
    __tablename__ = "food_shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String)

    # Relationship with food items
    food_items = relationship("FoodItem", back_populates="shop")


# Food Items Table
class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String)
    price = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)

    shop_id = Column(Integer, ForeignKey("food_shops.id"))

    # Relationships
    shop = relationship("FoodShop", back_populates="food_items")
    reviews = relationship("Review", back_populates="food_item")


# Reviews Table
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # True for sample reviews created by seed_reviews.py (so they can be cleared safely)
    is_demo = Column(Boolean, default=False)

    food_item_id = Column(Integer, ForeignKey("food_items.id"))

    # Relationship
    food_item = relationship("FoodItem", back_populates="reviews")
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend import models, services
from backend.database import ensure_schema, get_db


# Structure for submitting student reviews
class ReviewCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    student_name: str = Field(min_length=2, max_length=100)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=2, max_length=1000)


# Create database tables (and add newer columns) if needed
ensure_schema()

app = FastAPI(
    title="CampusBites API",
    description="UPES Food Discovery Platform",
    version="2.0.0"
)

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "Welcome to CampusBites!",
        "status": "API is running successfully",
        "website": "/app/"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# ---------------- Food shops ----------------

@app.get("/shops")
def get_shops(db: Session = Depends(get_db)):
    """All shops with item count, price range, categories and rating."""
    return services.list_shops(db)


@app.get("/shops/{shop_id}")
def get_shop(shop_id: int, db: Session = Depends(get_db)):
    shop = services.get_shop(db, shop_id)
    if shop is None:
        raise HTTPException(status_code=404, detail="Food shop not found")
    return shop


# ---------------- Menu items ----------------

@app.get("/items")
def get_items(db: Session = Depends(get_db)):
    return services.list_items(db)


@app.get("/items/search")
def search_items(
    name: str = None,
    category: str = None,
    shop: str = None,
    shop_id: int = None,
    max_price: float = None,
    sort: str = Query("name", pattern="^(name|price_asc|price_desc|rating)$"),
    db: Session = Depends(get_db),
):
    return services.list_items(db, name, category, shop, shop_id, max_price, sort)


# ---------------- Find a meal within a budget ----------------

@app.get("/meal-finder")
def meal_finder(
    budget: float = Query(gt=0, le=5000),
    courses: str = Query(None, description="Comma separated: meal,snack,drink,dessert"),
    shop: str = None,
    same_shop: bool = True,
    sort: str = Query("match", pattern="^(match|rating|cheapest)$"),
    limit: int = Query(12, ge=1, le=40),
    db: Session = Depends(get_db),
):
    chosen = [c.strip().lower() for c in courses.split(",")] if courses else []
    return services.meal_finder(db, budget, chosen, shop, same_shop, sort, limit)


# Older endpoint, kept for compatibility
@app.get("/recommendations")
def get_recommendations(
    budget: float,
    category: str = None,
    shop: str = None,
    db: Session = Depends(get_db),
):
    items = services.list_items(db, category=category, shop=shop,
                                max_price=budget, sort="price_asc")
    return {"budget": budget, "total_recommendations": len(items),
            "recommendations": items}


# ---------------- Reviews ----------------

@app.post("/items/{item_id}/reviews")
def add_review(item_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    item = db.query(models.FoodItem).filter(models.FoodItem.id == item_id).first()

    if item is None:
        raise HTTPException(status_code=404, detail="Food item not found")

    new_review = models.Review(
        student_name=review.student_name,
        rating=review.rating,
        comment=review.comment,
        food_item_id=item_id,
        is_demo=False,
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    return {
        "message": "Review submitted successfully!",
        "review_id": new_review.id,
        "food_item": item.name,
        "student_name": new_review.student_name,
        "rating": new_review.rating,
        "comment": new_review.comment,
    }


@app.get("/items/{item_id}/reviews")
def get_reviews(item_id: int, db: Session = Depends(get_db)):
    data = services.item_reviews(db, item_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Food item not found")
    return data


@app.get("/reviews/recent")
def recent_reviews(limit: int = Query(8, ge=1, le=50), shop_id: int = None,
                   db: Session = Depends(get_db)):
    return services.recent_reviews(db, limit, shop_id)


@app.get("/analytics/reviews")
def review_analytics(shop_id: int = None, days: int = Query(30, ge=7, le=90),
                     db: Session = Depends(get_db)):
    """Everything the review dashboard needs, in one call."""
    return services.review_analytics(db, shop_id, days)


# ---------------- Website ----------------
# The website is also served by the backend: http://127.0.0.1:8000/app/
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

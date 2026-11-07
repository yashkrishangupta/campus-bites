"""
Adds sample (demo) reviews so the review charts have something to show.

    python -m backend.seed_reviews            add ~300 demo reviews
    python -m backend.seed_reviews --clear    remove ONLY the demo reviews

Real reviews written on the website are never touched by --clear.
"""

import random
import sys
from datetime import datetime, timedelta, timezone

from backend import models
from backend.database import SessionLocal, ensure_schema

random.seed(42)

# Rough "how good is this shop" so the charts show some variety
SHOP_QUALITY = {
    "Annapurna": 4.3, "Appetite Rolls": 4.0, "Chai Garam": 3.9,
    "Food Court": 3.2, "Frisco": 4.4, "Tulips": 3.6,
}

NAMES = ["Aarav", "Ananya", "Rohan", "Isha", "Kabir", "Meera", "Vihaan", "Diya",
         "Arjun", "Sneha", "Yash", "Riya", "Karan", "Tanvi", "Aditya", "Naina",
         "Harsh", "Pooja", "Dev", "Simran", "Nikhil", "Kriti"]

COMMENTS = {
    5: ["Absolutely loved this, will order again!", "Best thing on the menu.",
        "Tasty, fresh and totally worth the price.", "My go-to between lectures.",
        "Great portion and great taste."],
    4: ["Really good, just a little wait at peak time.", "Tasty and good value.",
        "Solid choice, would recommend.", "Liked it a lot, nice portion."],
    3: ["It was okay, nothing special.", "Decent for the price.",
        "Average taste, but filling.", "Good some days, hit or miss on others."],
    2: ["Quite bland and a bit oily.", "Portion felt small for the price.",
        "Was cold when it arrived."],
    1: ["Did not enjoy this at all.", "Poor quality, would not order again."],
}


def seed():
    ensure_schema()
    db = SessionLocal()
    try:
        if db.query(models.Review).filter(models.Review.is_demo == True).count():  # noqa: E712
            print("Demo reviews already exist. Use --clear first to recreate them.")
            return

        items = db.query(models.FoodItem).all()
        if not items:
            print("No menu items found. Run first:  python -m backend.import_data")
            return
        now = datetime.now(timezone.utc)
        total = 0

        for item in random.sample(items, min(120, len(items))):
            base = SHOP_QUALITY.get(item.shop.name, 3.7)
            for _ in range(random.choice([1, 1, 2, 2, 3, 4, 6])):
                rating = max(1, min(5, round(random.gauss(base, 0.9))))
                age = random.random() ** 1.4 * 29          # more recent reviews
                db.add(models.Review(
                    student_name=random.choice(NAMES),
                    rating=rating,
                    comment=random.choice(COMMENTS[rating]),
                    food_item_id=item.id,
                    is_demo=True,
                    created_at=now - timedelta(days=age, hours=random.random() * 12),
                ))
                total += 1

        db.commit()
        print(f"Added {total} demo reviews.")
    finally:
        db.close()


def clear():
    ensure_schema()
    db = SessionLocal()
    try:
        removed = db.query(models.Review).filter(models.Review.is_demo == True).delete()  # noqa: E712
        db.commit()
        print(f"Removed {removed} demo reviews.")
    finally:
        db.close()


if __name__ == "__main__":
    clear() if "--clear" in sys.argv else seed()

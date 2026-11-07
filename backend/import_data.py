
import pandas as pd
from pathlib import Path

from backend.database import SessionLocal, ensure_schema
from backend.models import FoodShop, FoodItem

# Locate the master CSV file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "campusbites_master.csv"

# Make sure the tables exist, then create a database session
ensure_schema()
db = SessionLocal()

try:
    # Read the CSV file
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    print("CSV loaded successfully!")
    print("Total menu items:", len(df))
    print("Columns:", df.columns.tolist())

    # Avoid importing the same menu items twice
    if db.query(FoodItem).count() > 0:
        print("Menu items already exist in the database.")
    else:
        # Create shops and menu items
        for _, row in df.iterrows():

            shop_name = str(row["Shop Name"]).strip()

            # Find the shop or create it
            shop = db.query(FoodShop).filter(
                FoodShop.name == shop_name
            ).first()

            if shop is None:
                shop = FoodShop(name=shop_name)
                db.add(shop)
                db.flush()

            # Create a food item
            food_item = FoodItem(
                name=str(row["Item to Buy"]).strip(),
                category=str(row["Category"]).strip(),
                price=float(row["Price"]),
                shop_id=shop.id
            )

            db.add(food_item)

        # Save everything to the database
        db.commit()

        print("Import completed successfully!")
        print("Total food items imported:", db.query(FoodItem).count())
        print("Total shops imported:", db.query(FoodShop).count())

except Exception as e:
    db.rollback()
    print("Error during import:", e)

finally:
    db.close()

# 🍽️ CampusBites – UPES Food Discovery Platform

**Discover. Compare. Eat.**

CampusBites helps UPES students explore food shops, browse their menus, find meals that fit a budget, and read (and write) honest reviews.

The website has **two main sections**, plus student reviews with charts:

1. **Food Shops** – open any shop to see its full menu with prices, ratings, **See Reviews** and **Review** buttons on every dish.
2. **Find Meal in My Budget** – enter a budget and what you're craving; get complete meals (e.g. main + drink + dessert) ranked by price fit and student ratings.
3. **Reviews** – **Give Review** form plus a live **Review Insights** dashboard built from student reviews.

## ✨ Pages

| Page | What it does |
|---|---|
| `index.html` | Home: hero (Explore Food Shops / Find Meal in My Budget / **Give Review**), shop cards, quick budget box, review highlights |
| `shop.html?id=…` | A shop's menu: search, category chips, sort, max price, **See Reviews** / **Review** on each dish |
| `meal.html` | Meal finder: budget, cravings (meal / snack / drink / dessert), shop, one-shop toggle, sort |
| `reviews.html` | **Give Review** form + Review Insights charts + latest reviews |

## 📊 Review visualizations

Built from real student reviews (plain SVG/CSS, no external libraries):

- Rating breakdown (5★ to 1★) and a "student mood" donut
- Shop leaderboard and food-category ratings
- Reviews per day with the average-rating trend
- Price vs. rating scatter ("does paying more get you better food?")
- Top rated, most reviewed and needs-improvement dishes
- Filter the whole dashboard by shop

## 💡 How the meal finder works

- **Courses:** Meal = Main Course / Fast Food / South Indian, Snack = Snacks / Soups, Drink = Beverages, Dessert = Desserts.
- It builds combinations with **one dish per chosen course** whose total is within the budget. Turn off "Get everything from one shop" to mix shops.
- **Best match** blends how well the meal uses your budget (35%) with student ratings (65%). **Highest rated** and **Cheapest first** are also available.
- Ratings use a weighted average, so one 5★ review doesn't beat a dish with many 4.5★ reviews. Unrated dishes count as 3.5.
- If nothing fits, it tells you the cheapest possible meal and how much more you need.
- With no craving selected it simply lists single dishes within your budget.

## 🛠️ Tech Stack

Python · FastAPI · SQLAlchemy · SQLite · Pandas (data cleaning) · HTML / CSS / JavaScript

## 📊 Dataset

363 menu items from 6 UPES outlets (Annapurna, Appetite Rolls, Chai Garam, Food Court, Frisco, Tulips), with Shop Name, Item, Category and Price.

## 🏗️ Project Structure

```text
CampusBites/
├── backend/
│   ├── main.py            API routes
│   ├── services.py        shop stats, meal finder, review analytics
│   ├── models.py          database tables
│   ├── database.py        connection + automatic schema update
│   ├── import_data.py     loads the menu CSV into SQLite
│   ├── seed_reviews.py    optional demo reviews for the charts
│   └── requirements.txt
├── data/ (raw + processed)
├── notebooks/
└── frontend/
    ├── index.html  shop.html  meal.html  reviews.html
    ├── style.css   script.js (shared)  charts.js
```

## ⚙️ Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r backend/requirements.txt

python -m backend.import_data     # first time only: loads the menu
python -m uvicorn backend.main:app --reload
```

Open the website at **http://127.0.0.1:8000/app/** (API docs: `/docs`).
You can also open `frontend/index.html` with Live Server; it talks to the backend on port 8000.

Your existing `campusbites.db` keeps working. A new column is added automatically on startup and no data is lost.

### Demo reviews (optional)

The review charts need reviews to show anything. To fill them with ~350 sample reviews:

```bash
python -m backend.seed_reviews            # add demo reviews
python -m backend.seed_reviews --clear    # remove ONLY the demo reviews
```

Real reviews written on the website are never removed by `--clear`.

## 🔗 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/shops` | Shops with item count, price range, categories, rating |
| GET | `/shops/{id}` | One shop's details |
| GET | `/items/search` | Dishes with ratings: `name, category, shop, shop_id, max_price, sort` |
| GET | `/meal-finder` | Budget meals: `budget, courses, shop, same_shop, sort, limit` |
| GET | `/items/{id}/reviews` | Reviews, average and rating breakdown for a dish |
| POST | `/items/{id}/reviews` | Submit a review |
| GET | `/reviews/recent` | Latest reviews (optional `shop_id`) |
| GET | `/analytics/reviews` | All data for the review charts (optional `shop_id`) |
| GET | `/items`, `/recommendations` | Earlier endpoints, kept for compatibility |

## 🔮 Future Enhancements

- Student login and verified reviews
- Veg / non-veg and spice filters (needs the menu data to include them)
- Photos with reviews
- Deployment for campus-wide access

---

**CampusBites – Discover. Compare. Eat.**

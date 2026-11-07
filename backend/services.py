"""
CampusBites business logic.

Kept separate from the FastAPI routes (main.py) so it is easy to read and test.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from itertools import product

from sqlalchemy import func

from backend import models

# A dish with no reviews is treated as "average" (3.5) and every review pulls
# it towards its real rating. This stops one 5-star review beating 40 4.5-star ones.
PRIOR_MEAN = 3.5
PRIOR_WEIGHT = 2

# Meal finder: which menu categories count as which "course"
COURSES = {
    "meal": ["Main Course", "Fast Food", "South Indian"],
    "snack": ["Snacks", "Soups"],
    "drink": ["Beverages"],
    "dessert": ["Desserts"],
}
COURSE_OF_CATEGORY = {
    category.lower(): course
    for course, categories in COURSES.items()
    for category in categories
}


def clean(text):
    return " ".join(text.strip().split()) if text else None


def bayes(average, count):
    if not count:
        return PRIOR_MEAN
    return (count * average + PRIOR_WEIGHT * PRIOR_MEAN) / (count + PRIOR_WEIGHT)


# ------------------------------------------------------------------
# Ratings and items
# ------------------------------------------------------------------

def rating_map(db):
    """item_id -> (average rating, number of reviews)"""
    rows = (
        db.query(
            models.Review.food_item_id,
            func.avg(models.Review.rating),
            func.count(models.Review.id),
        )
        .group_by(models.Review.food_item_id)
        .all()
    )
    return {item_id: (round(avg, 2), count) for item_id, avg, count in rows}


def item_dict(item, ratings):
    avg, count = ratings.get(item.id, (None, 0))
    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "price": item.price,
        "shop_id": item.shop_id,
        "shop_name": item.shop.name,
        "shop": item.shop.name,
        "average_rating": avg,
        "total_reviews": count,
    }


def list_items(db, name=None, category=None, shop=None, shop_id=None,
               max_price=None, sort="name"):
    query = db.query(models.FoodItem).join(models.FoodShop)

    if clean(name):
        query = query.filter(models.FoodItem.name.ilike(f"%{clean(name)}%"))
    if clean(category):
        query = query.filter(models.FoodItem.category.ilike(clean(category)))
    if clean(shop):
        query = query.filter(models.FoodShop.name.ilike(clean(shop)))
    if shop_id is not None:
        query = query.filter(models.FoodItem.shop_id == shop_id)
    if max_price is not None:
        query = query.filter(models.FoodItem.price <= max_price)

    ratings = rating_map(db)
    items = [item_dict(i, ratings) for i in query.all()]

    if sort == "price_asc":
        items.sort(key=lambda i: (i["price"], i["name"]))
    elif sort == "price_desc":
        items.sort(key=lambda i: (-i["price"], i["name"]))
    elif sort == "rating":
        items.sort(key=lambda i: (-bayes(i["average_rating"], i["total_reviews"]),
                                  -i["total_reviews"], i["name"]))
    else:
        items.sort(key=lambda i: (i["category"] or "", i["name"]))
    return items


# ------------------------------------------------------------------
# Shops
# ------------------------------------------------------------------

def shop_summary(shop, ratings):
    items = shop.food_items
    prices = [i.price for i in items]

    categories = defaultdict(int)
    for i in items:
        categories[i.category or "Other"] += 1

    total_stars = sum(ratings[i.id][0] * ratings[i.id][1] for i in items if i.id in ratings)
    total_reviews = sum(ratings[i.id][1] for i in items if i.id in ratings)

    return {
        "id": shop.id,
        "name": shop.name,
        "location": shop.location,
        "total_items": len(items),
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "avg_price": round(sum(prices) / len(prices)) if prices else None,
        "categories": [
            {"name": n, "count": c}
            for n, c in sorted(categories.items(), key=lambda x: -x[1])
        ],
        "average_rating": round(total_stars / total_reviews, 2) if total_reviews else None,
        "total_reviews": total_reviews,
    }


def list_shops(db):
    ratings = rating_map(db)
    shops = db.query(models.FoodShop).order_by(models.FoodShop.name).all()
    return [shop_summary(s, ratings) for s in shops]


def get_shop(db, shop_id):
    shop = db.query(models.FoodShop).filter(models.FoodShop.id == shop_id).first()
    return shop_summary(shop, rating_map(db)) if shop else None


# ------------------------------------------------------------------
# Meal finder
# ------------------------------------------------------------------

def _score(total, quality, budget):
    """Blend of 'uses the budget well' and 'tastes good' (0 to 1)."""
    return 0.35 * (total / budget) + 0.65 * (quality / 5)


def _trim(pool, budget, cap):
    """Keep the pool small: best rated + cheapest items within budget."""
    affordable = [i for i in pool if i["price"] <= budget]
    best = sorted(affordable, key=lambda i: (-i["quality"], i["price"]))[:int(cap * 0.6)]
    cheap = sorted(affordable, key=lambda i: i["price"])[:int(cap * 0.4)]
    return list({i["id"]: i for i in best + cheap}.values())


def meal_finder(db, budget, courses=None, shop=None, same_shop=True,
                sort="match", limit=12):
    ratings = rating_map(db)

    query = db.query(models.FoodItem).join(models.FoodShop).filter(
        models.FoodItem.is_available == True  # noqa: E712
    )
    if clean(shop):
        query = query.filter(models.FoodShop.name.ilike(clean(shop)))

    items = []
    for row in query.all():
        d = item_dict(row, ratings)
        d["quality"] = round(bayes(d["average_rating"], d["total_reviews"]), 2)
        items.append(d)

    courses = [c for c in (courses or []) if c in COURSES]
    courses = list(dict.fromkeys(courses))  # remove duplicates, keep order

    result = {"budget": budget, "courses": courses, "sort": sort, "same_shop": same_shop}

    # ---- No course chosen: simply list single items within budget ----
    if not courses:
        within = [i for i in items if i["price"] <= budget]
        for i in within:
            i["score"] = _score(i["price"], i["quality"], budget)

        if sort == "cheapest":
            within.sort(key=lambda i: (i["price"], -i["quality"]))
        elif sort == "rating":
            within.sort(key=lambda i: (-i["quality"], -i["total_reviews"], i["price"]))
        else:
            within.sort(key=lambda i: -i["score"])

        return {**result, "mode": "items", "total_found": len(within),
                "results": within[:limit]}

    # ---- Courses chosen: build combos (one dish per course) ----
    pools = {c: [] for c in courses}
    for i in items:
        course = COURSE_OF_CATEGORY.get((i["category"] or "").lower())
        if course in pools:
            pools[course].append({**i, "course": course})

    # Groups of pools that may be combined together
    groups = []
    if same_shop:
        by_shop = defaultdict(lambda: {c: [] for c in courses})
        for course, pool in pools.items():
            for i in pool:
                by_shop[i["shop_id"]][course].append(i)
        groups = [g for g in by_shop.values() if all(g[c] for c in courses)]
    elif all(pools[c] for c in courses):
        groups = [pools]

    if not groups:
        return {**result, "mode": "combo", "total_found": 0, "results": [],
                "cheapest_possible": None}

    # Cheapest possible meal, so we can tell the student what they would need
    cheapest_possible = min(
        sum(min(i["price"] for i in g[c]) for c in courses) for g in groups
    )

    # Limit how many dishes per course are combined (keeps the search fast)
    cap = max(10, int(40000 ** (1 / len(courses))))

    combos = []
    for g in groups:
        lists = [_trim(g[c], budget, cap) for c in courses]
        if not all(lists):
            continue
        for combo in product(*lists):
            total = sum(i["price"] for i in combo)
            if total > budget:
                continue
            quality = sum(i["quality"] for i in combo) / len(combo)
            combos.append({
                "items": list(combo),
                "shops": sorted({i["shop_name"] for i in combo}),
                "total_price": total,
                "left": round(budget - total, 2),
                "quality": round(quality, 2),
                "score": _score(total, quality, budget),
            })

    if sort == "cheapest":
        order = lambda c: (c["total_price"], -c["quality"])
    elif sort == "rating":
        order = lambda c: (-c["quality"], -c["total_price"])
    else:
        order = lambda c: -c["score"]
    combos.sort(key=order)

    # Variety: a dish appears at most twice and no single shop fills the list.
    shop_cap = max(2, -(-limit // 3))
    picked, used_item, used_shop = [], defaultdict(int), defaultdict(int)

    for c in combos:
        shop_key = tuple(c["shops"])
        if any(used_item[i["id"]] >= 2 for i in c["items"]) or used_shop[shop_key] >= shop_cap:
            continue
        picked.append(c)
        used_shop[shop_key] += 1
        for i in c["items"]:
            used_item[i["id"]] += 1
        if len(picked) == limit:
            break

    # Few dishes available (e.g. one shop with a single dessert): relax the rules
    if len(picked) < limit:
        chosen = {id(c) for c in picked}
        picked += [c for c in combos if id(c) not in chosen][: limit - len(picked)]

    picked.sort(key=order)

    return {**result, "mode": "combo", "total_found": len(combos),
            "results": picked, "cheapest_possible": cheapest_possible}


# ------------------------------------------------------------------
# Reviews and analytics
# ------------------------------------------------------------------

def item_reviews(db, item_id):
    item = db.query(models.FoodItem).filter(models.FoodItem.id == item_id).first()
    if item is None:
        return None

    reviews = (
        db.query(models.Review)
        .filter(models.Review.food_item_id == item_id)
        .order_by(models.Review.created_at.desc(), models.Review.id.desc())
        .all()
    )
    distribution = {str(n): 0 for n in range(1, 6)}
    for r in reviews:
        distribution[str(r.rating)] += 1

    return {
        "food_item": item.name,
        "shop_name": item.shop.name,
        "price": item.price,
        "total_reviews": len(reviews),
        "average_rating": (
            round(sum(r.rating for r in reviews) / len(reviews), 2) if reviews else None
        ),
        "distribution": distribution,
        "reviews": [
            {
                "student_name": r.student_name,
                "rating": r.rating,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reviews
        ],
    }


def _review_rows(db, shop_id=None):
    query = (
        db.query(models.Review, models.FoodItem, models.FoodShop)
        .join(models.FoodItem, models.Review.food_item_id == models.FoodItem.id)
        .join(models.FoodShop, models.FoodItem.shop_id == models.FoodShop.id)
    )
    if shop_id is not None:
        query = query.filter(models.FoodShop.id == shop_id)
    return query.all()


def recent_reviews(db, limit=8, shop_id=None):
    rows = _review_rows(db, shop_id)
    rows.sort(key=lambda r: (r[0].created_at or datetime.min, r[0].id), reverse=True)
    return [
        {
            "student_name": r.student_name,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "item_id": item.id,
            "item_name": item.name,
            "shop_name": shop.name,
        }
        for r, item, shop in rows[:limit]
    ]


def _mean(values):
    return round(sum(values) / len(values), 2) if values else None


def review_analytics(db, shop_id=None, days=30):
    rows = _review_rows(db, shop_id)

    distribution = {str(n): 0 for n in range(1, 6)}
    by_shop, by_category, by_item, by_day = (defaultdict(list) for _ in range(4))
    meta = {}

    for review, item, shop in rows:
        distribution[str(review.rating)] += 1
        by_shop[shop.name].append(review.rating)
        by_category[item.category or "Other"].append(review.rating)
        by_item[item.id].append(review.rating)
        meta[item.id] = (item, shop)
        if review.created_at:
            by_day[review.created_at.date()].append(review.rating)

    ratings = [r.rating for r, _, _ in rows]

    items_stats = []
    for item_id, values in by_item.items():
        item, shop = meta[item_id]
        avg = _mean(values)
        items_stats.append({
            "id": item.id, "name": item.name, "shop": shop.name,
            "category": item.category, "price": item.price,
            "average_rating": avg, "total_reviews": len(values),
            "quality": bayes(avg, len(values)),
        })

    top = sorted(items_stats, key=lambda i: (-i["quality"], -i["total_reviews"]))[:5]
    needs_love = sorted(
        [i for i in items_stats if i["total_reviews"] >= 2 and i["average_rating"] < 4],
        key=lambda i: (i["quality"], -i["total_reviews"]),
    )[:5]
    most_reviewed = sorted(items_stats, key=lambda i: -i["total_reviews"])[:5]

    today = datetime.now(timezone.utc).date()
    trend = []
    for n in range(days - 1, -1, -1):
        day = today - timedelta(days=n)
        values = by_day.get(day, [])
        trend.append({"date": day.isoformat(), "count": len(values), "average": _mean(values)})

    return {
        "totals": {
            "reviews": len(ratings),
            "dishes_reviewed": len(by_item),
            "average_rating": _mean(ratings),
            "positive": sum(1 for r in ratings if r >= 4),
            "neutral": sum(1 for r in ratings if r == 3),
            "negative": sum(1 for r in ratings if r <= 2),
        },
        "distribution": distribution,
        "by_shop": sorted(
            [{"shop": n, "average_rating": _mean(v), "reviews": len(v)}
             for n, v in by_shop.items()],
            key=lambda x: -x["average_rating"],
        ),
        "by_category": sorted(
            [{"category": n, "average_rating": _mean(v), "reviews": len(v)}
             for n, v in by_category.items()],
            key=lambda x: -x["average_rating"],
        ),
        "top_items": [{k: v for k, v in i.items() if k != "quality"} for i in top],
        "needs_love": [{k: v for k, v in i.items() if k != "quality"} for i in needs_love],
        "most_reviewed": [{k: v for k, v in i.items() if k != "quality"} for i in most_reviewed],
        "price_vs_rating": [
            {k: i[k] for k in ("name", "shop", "price", "average_rating", "total_reviews")}
            for i in items_stats
        ],
        "trend": trend,
    }

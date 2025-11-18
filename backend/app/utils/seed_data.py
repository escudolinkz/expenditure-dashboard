from app.database import SessionLocal
from app.models import Category


def seed_default_categories():
    """Seed default spending categories"""
    db = SessionLocal()

    default_categories = [
        {"name": "Groceries", "color": "#4CAF50", "icon": "shopping_cart"},
        {"name": "Dining", "color": "#FF9800", "icon": "restaurant"},
        {"name": "Transport", "color": "#2196F3", "icon": "directions_car"},
        {"name": "Shopping", "color": "#E91E63", "icon": "shopping_bag"},
        {"name": "Utilities", "color": "#9C27B0", "icon": "electric_bolt"},
        {"name": "Entertainment", "color": "#F44336", "icon": "movie"},
        {"name": "Healthcare", "color": "#00BCD4", "icon": "local_hospital"},
        {"name": "Subscriptions", "color": "#607D8B", "icon": "repeat"},
        {"name": "Travel", "color": "#009688", "icon": "flight"},
        {"name": "Fitness", "color": "#CDDC39", "icon": "fitness_center"},
        {"name": "Education", "color": "#3F51B5", "icon": "school"},
        {"name": "Insurance", "color": "#795548", "icon": "security"},
        {"name": "Bills", "color": "#FF5722", "icon": "receipt"},
        {"name": "Personal Care", "color": "#8BC34A", "icon": "spa"},
        {"name": "Gifts", "color": "#FFC107", "icon": "card_giftcard"},
        {"name": "Other", "color": "#9E9E9E", "icon": "more_horiz"},
    ]

    try:
        for cat_data in default_categories:
            # Check if category already exists
            existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not existing:
                category = Category(**cat_data)
                db.add(category)

        db.commit()
        print(f"Seeded {len(default_categories)} default categories")
    except Exception as e:
        print(f"Error seeding categories: {e}")
        db.rollback()
    finally:
        db.close()

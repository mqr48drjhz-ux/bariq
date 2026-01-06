"""
Initialize database - run migrations and seed data
"""
import os
import sys

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db
from flask_migrate import upgrade

app = create_app()

with app.app_context():
    print("Running database migrations...")
    upgrade()
    print("Migrations complete!")

    # Check if data already exists
    from app.models import Customer
    if Customer.query.first() is None:
        print("Seeding database...")
        # Import and run the seed function
        from scripts.seed_data import seed_all
        seed_all()
        print("Seeding complete!")
    else:
        print("Database already has data, skipping seed.")

    print("Database initialization complete!")

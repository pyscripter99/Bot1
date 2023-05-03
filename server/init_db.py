from flask import Flask
from models import db, Client
import datetime

# Create the Flask app and configure it
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///connections.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)
with app.app_context():
    db.drop_all()
    # Create the database and the tables
    db.create_all()

    # Commit the changes
    db.session.commit()

print("Database initialized.")

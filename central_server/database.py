from flask import Flask

from models import db
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
db.init_app(app)

def init_db():
    with app.app_context():
        db.create_all()

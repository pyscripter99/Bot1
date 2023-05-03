from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    id = db.Column(db.String, nullable=False, primary_key=True, unique=True)
    username = db.Column(db.String)
    hostname = db.Column(db.String)
    ip_addr = db.Column(db.String)
    sid = db.Column(db.String, unique=True)
    first_seen = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    connected = db.Column(db.Boolean)

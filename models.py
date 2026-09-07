from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Scan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    books = db.relationship("DetectedBook", backref="scan", cascade="all, delete-orphan")
    issues = db.relationship("Issue", backref="scan", cascade="all, delete-orphan")


class DetectedBook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scan.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    shelf_row = db.Column(db.Integer, nullable=False)


class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scan.id"), nullable=False)
    type = db.Column(db.String(40), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(20), nullable=False)

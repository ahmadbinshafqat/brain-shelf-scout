from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Scan(db.Model):
    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    books = db.relationship(
        "DetectedBook",
        back_populates="scan",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="DetectedBook.position",
    )
    issues = db.relationship(
        "Issue",
        back_populates="scan",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Issue.id",
    )

    @property
    def book_count(self):
        return len(self.books)

    @property
    def issue_count(self):
        return len(self.issues)

    @property
    def has_issues(self):
        return self.issue_count > 0


class DetectedBook(db.Model):
    __tablename__ = "detected_books"

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scans.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    series = db.Column(db.String(255), nullable=True)
    volume = db.Column(db.Integer, nullable=True)
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    shelf_row = db.Column(db.Integer, nullable=False, default=1)
    position = db.Column(db.Integer, nullable=False, default=0)
    color_hex = db.Column(db.String(16), nullable=False, default="#999999")

    scan = db.relationship("Scan", back_populates="books")

    @property
    def confidence_percent(self):
        return round((self.confidence or 0) * 100)

    @property
    def series_label(self):
        if self.series and self.volume:
            return f"{self.series} Vol. {self.volume}"
        if self.series:
            return self.series
        return "Standalone"


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scans.id"), nullable=False, index=True)
    issue_type = db.Column(db.String(80), nullable=False)
    severity = db.Column(db.String(30), nullable=False, default="info")
    message = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(255), nullable=True)
    series = db.Column(db.String(255), nullable=True)

    scan = db.relationship("Scan", back_populates="issues")

    @property
    def display_type(self):
        return (self.issue_type or "issue").replace("_", " ").title()

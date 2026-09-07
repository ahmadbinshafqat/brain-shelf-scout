import os
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename

from models import db, Scan, DetectedBook, Issue
from services.detector import detect_books
from services.issues import analyze_issues

load_dotenv()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///shelf_scout.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "static/uploads")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH_MB", "8")) * 1024 * 1024

    db.init_app(app)

    upload_path = Path(app.config["UPLOAD_FOLDER"])
    upload_path.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        recent_scans = Scan.query.order_by(Scan.created_at.desc()).limit(5).all()
        return render_template("index.html", recent_scans=recent_scans)

    @app.route("/scan", methods=["POST"])
    def create_scan():
        if "image" not in request.files:
            flash("Please choose an image to upload.", "error")
            return redirect(url_for("index"))

        file = request.files["image"]
        if file.filename == "":
            flash("Please choose an image to upload.", "error")
            return redirect(url_for("index"))

        if not allowed_file(file.filename):
            flash("Upload a PNG, JPG, JPEG, or WEBP image.", "error")
            return redirect(url_for("index"))

        filename = secure_filename(file.filename)
        ext = filename.rsplit(".", 1)[1].lower()
        stored_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}.{ext}"
        saved_path = Path(app.config["UPLOAD_FOLDER"]) / stored_name
        file.save(saved_path)

        scan = Scan(image_url=f"/{saved_path.as_posix()}")
        db.session.add(scan)
        db.session.flush()

        detected = detect_books(saved_path)
        for book in detected:
            db.session.add(DetectedBook(scan_id=scan.id, **book))
        db.session.flush()

        issues = analyze_issues(detected)
        for issue in issues:
            db.session.add(Issue(scan_id=scan.id, **issue))
        db.session.commit()

        return redirect(url_for("results", scan_id=scan.id))

    @app.route("/scan/<int:scan_id>")
    def results(scan_id):
        scan = Scan.query.get_or_404(scan_id)
        books = DetectedBook.query.filter_by(scan_id=scan.id).order_by(DetectedBook.shelf_row, DetectedBook.x).all()
        issues = Issue.query.filter_by(scan_id=scan.id).order_by(Issue.severity.desc(), Issue.type).all()
        duplicate_titles = {clean_title(i.description) for i in issues if i.type == "duplicate"}
        return render_template("results.html", scan=scan, books=books, issues=issues, duplicate_titles=duplicate_titles)

    @app.route("/demo-image")
    def demo_image():
        path = generate_demo_image()
        return send_file(path, mimetype="image/png", as_attachment=False, download_name="shelf-scout-demo.png")

    return app


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def clean_title(description):
    match = re.search(r"Duplicate detected: (.+?) appears", description)
    return match.group(1) if match else description


def generate_demo_image():
    output_dir = Path("static/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "shelf-scout-demo.png"
    if output_path.exists():
        return output_path

    width, height = 1100, 620
    img = Image.new("RGB", (width, height), "#f6f0e6")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        small = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small = ImageFont.load_default()

    shelves = [(55, 80, 1010, 230), (55, 330, 1010, 480)]
    for x1, y1, x2, y2 in shelves:
        draw.rectangle([x1, y2, x2, y2 + 24], fill="#7a4e2b")
        draw.rectangle([x1 - 12, y1 - 20, x2 + 12, y2 + 28], outline="#8b5a2b", width=5)

    books = [
        (80, 85, 82, 145, "#bb3e03", "The Lunar\nGate Vol.1"),
        (168, 90, 76, 140, "#005f73", "Garden\nNotes"),
        (250, 82, 88, 148, "#ae2012", "The Lunar\nGate Vol.3"),
        (344, 98, 70, 132, "#6a994e", "Tiny\nHabits"),
        (420, 88, 72, 142, "#bb3e03", "The Lunar\nGate Vol.1"),
        (90, 335, 84, 145, "#3a86ff", "Python\nWeekend"),
        (180, 342, 78, 138, "#8338ec", "Deep Work\nDesk"),
        (264, 332, 88, 148, "#fb5607", "Home\nArchive"),
        (360, 340, 76, 140, "#ff006e", "Meal\nSystems"),
    ]
    for x, y, w, h, color, label in books:
        draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=color, outline="#222", width=2)
        lines = label.split("\n")
        ty = y + 14
        for line in lines:
            draw.text((x + 8, ty), line, fill="white", font=small)
            ty += 22

    draw.text((55, 25), "Shelf Scout demo shelf", fill="#3b2f2f", font=font)
    img.save(output_path)
    return output_path


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

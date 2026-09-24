import os
from pathlib import Path
from uuid import uuid4

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from models import db, DetectedBook, Issue, Scan
from services.detector import detect_books, generate_demo_shelf_image
from services.issues import analyze_issues

BASE_DIR = Path(__file__).resolve().parent
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///shelf_scout.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = os.environ.get("UPLOAD_FOLDER", "static/uploads")
    app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_CONTENT_LENGTH_MB", "8")) * 1024 * 1024

    upload_path = Path(app.config["UPLOAD_FOLDER"])
    if not upload_path.is_absolute():
        upload_path = BASE_DIR / upload_path
    upload_path.mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_PATH"] = upload_path

    db.init_app(app)

    with app.app_context():
        db.create_all()

    def allowed_file(filename):
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

    def scan_with_details(scan_id):
        return (
            Scan.query.options(joinedload(Scan.books), joinedload(Scan.issues))
            .filter(Scan.id == scan_id)
            .first_or_404()
        )

    def persist_scan(original_filename, image_relative_path, detections, issues):
        scan = Scan(
            original_filename=original_filename,
            image_path=image_relative_path,
        )
        db.session.add(scan)
        db.session.flush()

        for item in detections:
            book = DetectedBook(
                scan_id=scan.id,
                title=item.get("title", "Unknown title"),
                author=item.get("author", "Unknown author"),
                series=item.get("series"),
                volume=item.get("volume"),
                confidence=float(item.get("confidence", 0)),
                shelf_row=int(item.get("shelf_row", 1)),
                position=int(item.get("position", 0)),
                color_hex=item.get("color_hex", "#999999"),
            )
            db.session.add(book)

        db.session.flush()

        for item in issues:
            issue = Issue(
                scan_id=scan.id,
                issue_type=item.get("issue_type", item.get("type", "issue")),
                severity=item.get("severity", "info"),
                message=item.get("message", "Review this scan."),
                title=item.get("title"),
                series=item.get("series"),
            )
            db.session.add(issue)

        db.session.commit()
        return scan

    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            uploaded = request.files.get("shelf_image")
            if not uploaded or uploaded.filename == "":
                flash("Please choose a bookshelf image to scan.", "error")
                return redirect(url_for("index"))

            if not allowed_file(uploaded.filename):
                flash("Unsupported file type. Please upload a PNG, JPG, JPEG, or WEBP image.", "error")
                return redirect(url_for("index"))

            safe_name = secure_filename(uploaded.filename)
            unique_name = f"{uuid4().hex}_{safe_name}"
            destination = app.config["UPLOAD_PATH"] / unique_name
            uploaded.save(destination)

            image_relative_path = f"uploads/{unique_name}"
            detections = detect_books(str(destination))
            issues = analyze_issues(detections)
            scan = persist_scan(safe_name, image_relative_path, detections, issues)

            flash("Scan saved. You can reopen it anytime from Scan History.", "success")
            return redirect(url_for("scan_detail", scan_id=scan.id))

        recent_scans = Scan.query.order_by(Scan.created_at.desc()).limit(3).all()
        return render_template("index.html", recent_scans=recent_scans)

    @app.route("/history")
    def history():
        scans = Scan.query.order_by(Scan.created_at.desc()).all()
        return render_template("history.html", scans=scans)

    @app.route("/scans/<int:scan_id>")
    def scan_detail(scan_id):
        scan = scan_with_details(scan_id)
        books = sorted(scan.books, key=lambda book: (book.shelf_row or 0, book.position or 0, book.id))
        issues = sorted(scan.issues, key=lambda issue: (issue.severity or "", issue.issue_type or "", issue.id))
        return render_template(
            "scan_detail.html",
            scan=scan,
            books=books,
            issues=issues,
            from_history=request.args.get("from") == "history",
        )

    @app.route("/demo-image")
    def demo_image():
        image_bytes = generate_demo_shelf_image()
        return send_file(image_bytes, mimetype="image/png", as_attachment=True, download_name="shelf-scout-demo.png")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_ENV", "development") == "development")

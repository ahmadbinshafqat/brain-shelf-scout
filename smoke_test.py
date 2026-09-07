from pathlib import Path

from app import app, generate_demo_image
from models import db, Scan, DetectedBook, Issue
from services.detector import detect_books
from services.issues import analyze_issues


def main():
    with app.app_context():
        db.create_all()
        demo_path = generate_demo_image()
        books = detect_books(Path(demo_path))
        issues = analyze_issues(books)
        assert len(books) >= 6, f"expected at least 6 detected books, got {len(books)}"
        assert any(i["type"] == "duplicate" for i in issues), "expected duplicate issue"
        assert any(i["type"] == "series_gap" for i in issues), "expected series gap issue"

        scan = Scan(image_url="/static/demo/shelf-scout-demo.png")
        db.session.add(scan)
        db.session.flush()
        for book in books:
            db.session.add(DetectedBook(scan_id=scan.id, **book))
        for issue in issues:
            db.session.add(Issue(scan_id=scan.id, **issue))
        db.session.commit()
        print(f"Smoke test passed: scan #{scan.id}, {len(books)} books, {len(issues)} issues")


if __name__ == "__main__":
    main()

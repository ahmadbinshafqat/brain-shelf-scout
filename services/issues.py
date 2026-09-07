from collections import Counter, defaultdict

from services.catalog import CATALOG


def analyze_issues(detected_books):
    issues = []
    title_counts = Counter(book["title"] for book in detected_books)
    for title, count in title_counts.items():
        if count > 1:
            issues.append({
                "type": "duplicate",
                "description": f"Duplicate detected: {title} appears {count} times in this scan.",
                "severity": "high",
            })

    catalog_by_title = {item["title"]: item for item in CATALOG}
    present = defaultdict(set)
    for book in detected_books:
        item = catalog_by_title.get(book["title"])
        if item and item["series"] and item["volume"] is not None:
            present[item["series"]].add(item["volume"])

    full_series = defaultdict(set)
    for item in CATALOG:
        if item["series"] and item["volume"] is not None:
            full_series[item["series"]].add(item["volume"])

    for series, volumes in present.items():
        if len(volumes) < 2:
            continue
        low, high = min(volumes), max(volumes)
        missing_between = [v for v in range(low, high + 1) if v not in volumes]
        for volume in missing_between:
            if volume in full_series[series]:
                issues.append({
                    "type": "series_gap",
                    "description": f"Possible series gap: {series} volume {volume} is missing between volumes {low} and {high}.",
                    "severity": "medium",
                })

    if not detected_books:
        issues.append({
            "type": "low_detection",
            "description": "No book spines were detected. Try a straighter, brighter shelf photo.",
            "severity": "low",
        })

    return issues

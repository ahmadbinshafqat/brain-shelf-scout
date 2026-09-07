CATALOG = [
    {"title": "The Lunar Gate Vol. 1", "author": "Mira Sol", "series": "The Lunar Gate", "volume": 1, "rgb": (187, 62, 3)},
    {"title": "The Lunar Gate Vol. 2", "author": "Mira Sol", "series": "The Lunar Gate", "volume": 2, "rgb": (238, 155, 0)},
    {"title": "The Lunar Gate Vol. 3", "author": "Mira Sol", "series": "The Lunar Gate", "volume": 3, "rgb": (174, 32, 18)},
    {"title": "Garden Notes", "author": "Ivy Moss", "series": None, "volume": None, "rgb": (0, 95, 115)},
    {"title": "Tiny Habits at Home", "author": "Nora Bell", "series": None, "volume": None, "rgb": (106, 153, 78)},
    {"title": "Python Weekend", "author": "Sam Rivera", "series": None, "volume": None, "rgb": (58, 134, 255)},
    {"title": "Deep Work Desk", "author": "Len Stone", "series": None, "volume": None, "rgb": (131, 56, 236)},
    {"title": "Home Archive", "author": "Paula Chen", "series": None, "volume": None, "rgb": (251, 86, 7)},
    {"title": "Meal Systems", "author": "Ari Lane", "series": None, "volume": None, "rgb": (255, 0, 110)},
]


def nearest_catalog_book(rgb):
    best = None
    best_dist = 10**9
    for item in CATALOG:
        dist = sum((rgb[i] - item["rgb"][i]) ** 2 for i in range(3)) ** 0.5
        if dist < best_dist:
            best = item
            best_dist = dist
    confidence = max(0.35, min(0.99, 1 - best_dist / 260))
    return best, round(confidence, 2)

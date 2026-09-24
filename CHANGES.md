# Changes: Scan History and Detail Pages

## Added

- A `/history` page listing previous bookshelf scans stored in SQLite.
- A `/scans/<scan_id>` detail page that reopens any past scan's results.
- Navigation links in the base layout for Home and Scan History.
- History summary metadata, including scan date, detected book count, issue count, and uploaded image thumbnail.
- Reusable scan results rendering so newly uploaded scans and reopened scans share the same UI.
- Empty-state messaging when no scans have been uploaded yet.

## Modified

- `app.py`
  - Added `history()` and `scan_detail()` routes.
  - Redirects upload completion to the persistent scan detail URL.
  - Uses a shared query helper to load scans with detected books and issues.
- `models.py`
  - Added convenience relationships/helpers for scan history display while preserving existing persisted data.
- `templates/base.html`
  - Added top navigation and flash message rendering.
- `templates/index.html`
  - Added entry point link to scan history.
- `templates/results.html`
  - Updated copy/actions to support both new upload results and reopened historical scans.
- `templates/history.html`
  - New history list page.
- `templates/scan_detail.html`
  - New per-scan detail template that reuses the results view.
- `static/css/styles.css`
  - Added styles for navigation, history cards, metadata, thumbnails, badges, and actions.

## How to use

Run the existing app as before:

```bash
python app.py
```

Then open:

- Home/upload: <http://127.0.0.1:5000/>
- Scan history: <http://127.0.0.1:5000/history>

Upload a bookshelf image, then revisit it later from Scan History without re-uploading the image.

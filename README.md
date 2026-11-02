# SALST PWA — Local Demo

## Structure
- `frontend/` — PWA, simulator controller and browser assets.
- `backend/` — Flask API, dependencies and local `.env` configuration.
- `database/` — PostgreSQL SQL files and optional CSV import helper.
- `data/` — demonstration CSV records (not frontend code).
- `tags/` — four Python simulated cattle tags.
- `start.sh` — launches local backend and simulators.
- `render.yaml` — optional future Render deployment.

## Run locally (Kubuntu)
1. Install Python 3, Python venv and PostgreSQL. Create the `salst` database and grant access to the configured database user.
2. Edit **`backend/.env`**. Set `SALST_DATABASE_URL` to your actual local PostgreSQL or Neon connection string. A local default (`dbname=salst user=bobo`) is provided for compatibility with the previous package; change it if your database uses different credentials.
3. From the project directory run `chmod +x start.sh && ./start.sh`.
4. Open `http://127.0.0.1:5000` and sign in. Open `http://127.0.0.1:5000/controller` for simulator control.
5. Save a farm grazing boundary in Profile → Farmer & Farm. **Tags intentionally wait until a boundary is configured.**

`start.sh` installs dependencies, imports demo CSV data without deleting existing telemetry, and starts all four simulators. All services use the same `SALST_INGEST_KEY` from `backend/.env`; you do not need Render for local operation. Do not share `.env` or commit it to Git.

### Reporting settings
Peace and emergency reporting intervals have independent **seconds / minutes / hours** selectors. The API stores intervals in seconds. Valid ranges are 5–86400 seconds (peace) and 5–3600 seconds (emergency). To see movement quickly during a demonstration, set a short peace interval (e.g., 5–15 seconds); manual drive/escape commands send updates about once per second.

### Network error troubleshooting
- Use the Flask URL above, **not** `file://` or a separate frontend dev server. The frontend uses same-origin `/api` calls.
- Verify `http://127.0.0.1:5000/api/health` returns JSON.
- Confirm PostgreSQL is reachable using `SALST_DATABASE_URL` in `backend/.env`.
- Watch `./start.sh` output for connection errors. If you use Neon, you need an internet connection.
- Browser map tiles and Leaflet assets require internet access.
- The simulator controller requires an authenticated PWA session in the same browser.

### Existing installations
Do not delete your old database. The schema initialiser adds missing structures, and the importer preserves existing reports. The old reporting intervals in an existing database are **not** overwritten automatically.

### Status
This package is a **software simulator and PWA**. The physical LR1121 ↔ E80 LoRa gateway, ESP32 firmware and battery-powered operation are not integrated or validated. Do not present simulated telemetry as verified physical radio results.


### November interface fixes
- Server now serves all frontend scripts (`v8.js`, `v9.js`, `v11.js`).
- Per-tag history returns 20 reports at a time; Load 20 more expands it.
- Activity lists registered tags with their last report time.
- Tag-history maps show the configured grazing boundary.
- Owners can reset an emergency from an expanded tag, if the backend permits it.
- Refresh the browser with Ctrl+Shift+R after updating.

## Frontend organization
The `frontend/` directory contains only `index.html` and `controller.html`.
The app-specific CSS and JavaScript are embedded directly in the HTML files.
PWA metadata, service worker, and icon are in `backend/pwa_assets/` and are served by Flask at their original URL paths.
Leaflet and map tiles still require network access.

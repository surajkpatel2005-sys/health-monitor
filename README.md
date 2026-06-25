# Personal Health & Wellness Monitoring System

A complete full-stack web application built with **Flask + MySQL + Bootstrap 5**,
designed as a BCA/college-level project submission.

## Tech Stack
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript, Bootstrap Icons, Google Font (Poppins)
- **Backend:** Python, Flask
- **Database:** MySQL
- **Charts:** Matplotlib + Seaborn (rendered as base64 images, no extra static files needed)
- **Auth:** Flask sessions + Werkzeug password hashing

## Folder Structure
```
health_monitor/
│
├── app.py                  # Main Flask application (all routes & logic)
├── config.py                # App configuration (DB credentials, secret key, uploads)
├── database.sql             # MySQL schema — run this first
├── requirements.txt          # Python dependencies
│
├── templates/
│   ├── base.html             # Shared layout (navbar, footer, flash messages)
│   ├── index.html            # Home page
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── bmi.html
│   ├── water.html
│   ├── weight.html
│   ├── sleep.html
│   ├── exercise.html
│   ├── reports.html
│   ├── 404.html
│   └── 500.html
│
└── static/
    ├── css/
    │   ├── style.css         # Main theme (colors, cards, components)
    │   └── responsive.css     # Media queries
    ├── js/
    │   ├── script.js          # Global JS (loader, flash auto-dismiss, password toggle)
    │   └── dashboard.js       # Dashboard-specific JS
    └── uploads/                # Profile picture uploads land here
```

## Setup Instructions

### 1. Install MySQL and create the database
```bash
mysql -u root -p < database.sql
```
This creates the `health_monitor_db` database and all 6 tables
(`users`, `health_profile`, `bmi_records`, `water_tracker`, `weight_tracker`,
`sleep_tracker`, `exercise_tracker`).

### 2. Create a virtual environment & install dependencies
```bash
cd health_monitor
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> Note: `mysqlclient` requires MySQL development headers.
> - Ubuntu/Debian: `sudo apt-get install python3-dev default-libmysqlclient-dev build-essential`
> - macOS: `brew install mysql-client pkg-config`
> - Windows: use the prebuilt wheel matching your Python version, or install via `pip install mysqlclient` after installing MySQL Connector/C.

### 3. Configure database credentials
Open `config.py` and update if needed (defaults to `root` / no password / `localhost`):
```python
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DB = 'health_monitor_db'
```
You can also set these as environment variables (`MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`).

### 4. Run the app
```bash
python app.py
```
Visit **http://127.0.0.1:5000** in your browser.

## Default Flow
1. Register a new account on `/register`
2. Log in on `/login`
3. Land on `/dashboard` — your health command center
4. Use the **Trackers** dropdown to log BMI, Water, Weight, Sleep, Exercise
5. Visit `/reports` to see auto-generated Matplotlib/Seaborn charts and export/print them

## Security Features
- Passwords hashed with Werkzeug (`generate_password_hash` / `check_password_hash`)
- All SQL queries use parameterized statements (no string concatenation) — SQL-injection safe
- Session-protected routes via a custom `@login_required` decorator
- Server-side input validation (email format, password strength, numeric checks)
- File upload restricted to image extensions only

## Notes for Submission
- All charts are generated dynamically per request using Matplotlib/Seaborn and embedded
  as base64 PNGs directly in the HTML — no chart image files are stored on disk.
- The Reports page has a "Export / Print Report" button that uses the browser's print
  dialog (with print-specific CSS in `responsive.css`) to let users save a PDF.
- A default avatar (via ui-avatars.com initials) is shown if no profile picture is uploaded.

# TrackMint

TrackMint is a Flask-based expense tracking web application built for the CITS5505/CITS3403 Agile Web Development group project. The application helps users record income, upload receipt-based expenses, organise shared expenses through groups, and view spending insights in a simple dashboard.

Tagline: **Track smart. Spend better.**

## Project purpose

Managing small daily expenses is difficult when income, receipts, shared costs, and spending habits are stored separately. TrackMint provides one web application where users can:

- create an account and securely log in;
- record income entries;
- add expenses with merchant, category, amount, date, notes, and optional receipt upload;
- upload receipt files such as images or PDFs;
- create groups with other users for shared expense tracking;
- split group expenses and track payment/settlement status;
- view dashboard summaries and spending insights;
- view a leaderboard based on expense tracking activity.

The application uses a client-server architecture. Flask handles the server-side routes, authentication, database operations, form processing, and file uploads. HTML, CSS, Jinja templates, and JavaScript are used on the client side to provide the user interface and interactive behaviour.

## Group members

Replace the placeholder values below with the final group details before submission.

| UWA ID | Name | GitHub username |
|---|---|---|
| 00000000 | Student 1 | github-username-1 |
| 00000000 | Student 2 | github-username-2 |
| 00000000 | Student 3 | github-username-3 |
| 00000000 | Student 4 | github-username-4 |

## Main features

### Authentication

Users can sign up, log in, and log out. Passwords are stored as hashes rather than plain text. Flask-Login is used to manage authenticated sessions.

### Dashboard

After logging in, users can access a dashboard showing their financial activity and summary information. The dashboard gives users a central place to navigate to income, expenses, insights, groups, and leaderboard features.

### Income tracking

Users can add, edit, and delete income records. Income data is stored in the SQLite database and linked to the logged-in user.

### Expense and receipt tracking

Users can create expense records with details such as merchant, category, amount, date, notes, and frequency. Receipt files can be uploaded and stored in the application’s static upload directory. Supported upload types include common image formats and PDFs.

### Groups and shared expenses

Users can create groups and add other registered users. Groups support shared expenses, member splits, settlement status, and comments. This satisfies the requirement for users to view and interact with data from other users.

### Insights

The insights page summarises spending patterns from stored income and expense data. It helps users better understand their financial behaviour.

### Leaderboard

The leaderboard ranks users based on activity points earned from adding expenses. The streak system tracks consecutive days of expense activity.

## Technology stack

The project uses the technologies allowed in the project specification:

- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-WTF / CSRFProtect
- SQLite
- HTML
- CSS
- JavaScript
- Jinja templates
- Pytest for automated tests

## Project structure

```text
AgileWebDevlopment-LAB/
├── app/
│   ├── auth/
│   │   └── routes.py
│   ├── groups/
│   │   └── routes.py
│   ├── income/
│   │   └── routes.py
│   ├── insights/
│   │   └── routes.py
│   ├── leaderboard/
│   │   └── routes.py
│   ├── main/
│   │   └── routes.py
│   ├── receipts/
│   │   └── routes.py
│   ├── static/
│   │   ├── css/
│   │   └── uploads/
│   ├── templates/
│   ├── extensions.py
│   ├── models.py
│   └── __init__.py
├── migrations/
├── tests/
│   ├── conftest.py
│   └── test_trackmint_core.py
├── config.py
├── run.py
└── README.md
```

## Setup instructions

These instructions assume Python 3.10 or later is installed.

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd AgileWebDevlopment-LAB
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

If a `requirements.txt` file is available, run:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available, install the required packages manually:

```bash
pip install Flask Flask-SQLAlchemy Flask-Migrate Flask-Login Flask-WTF pytest
```

### 4. Set environment variables

On Windows PowerShell:

```powershell
$env:FLASK_APP = "run.py"
$env:FLASK_CONFIG = "development"
$env:SECRET_KEY = "CITS5505"
```

On macOS/Linux:

```bash
export FLASK_APP=run.py
export FLASK_CONFIG=development
export SECRET_KEY=CITS5505
```

### 5. Set up the database

If the repository includes an existing development database, the application can be run directly. Otherwise, create or upgrade the database using Flask-Migrate:

```bash
flask db upgrade
```

If migrations are not available or the database needs to be created from the models during local development, use a Flask shell:

```bash
flask shell
```

Then run:

```python
from app.extensions import db
db.create_all()
exit()
```

### 6. Run the application

```bash
python run.py
```

Then open the application in a browser:

```text
http://127.0.0.1:5000/
```

## Running tests

The automated tests are located in the `tests/` directory. The current test suite uses `pytest` and a temporary in-memory SQLite database for test isolation.

Run all tests from the project root:

```bash
pytest -q
```

The test suite covers core functionality including:

- user registration;
- login rejection with incorrect password;
- valid group creation;
- creator group deletion;
- expense creation;
- leaderboard point updates;
- same-day streak behaviour;
- consecutive-day streak behaviour;
- invalid expense amount validation;
- user search behaviour.

## Security features

TrackMint includes the following security measures:

- passwords are stored using Werkzeug password hashing;
- Flask-Login manages user sessions;
- CSRF protection is enabled using Flask-WTF’s `CSRFProtect`;
- standard POST forms include CSRF tokens;
- JavaScript/AJAX requests include CSRF headers where required;
- uploaded files are restricted by extension and file size;
- session cookies are configured with HTTP-only behaviour.

CSRF is disabled only in the testing configuration so that automated tests can run without manually generating form tokens.

## Database models

The main database models include:

- `User`: stores account information, password hash, points, streaks, and upload activity;
- `Income`: stores user income records;
- `Receipt`: stores expense records and uploaded receipt filenames;
- `Group`: stores shared expense groups;
- `GroupMember`: stores members associated with each group;
- `ExpenseSplit`: stores split payment information for group expenses;
- `SettlementComment`: stores comments related to group settlements.

## File uploads

Receipt uploads are stored under:

```text
app/static/uploads/receipts/
```

Profile uploads are stored under:

```text
app/static/uploads/profiles/
```

The application creates these upload folders automatically when it starts.

## Known limitations and future improvements

The current application provides the core expense tracking, income tracking, group sharing, receipt upload, and leaderboard features. Future improvements could include:

- adding Selenium browser tests to extend automated UI testing;
- improving receipt text extraction using OCR;
- adding stronger analytics and charts;
- adding recurring expense reminders;
- adding export functionality for expenses and income;
- improving group permission controls and member validation;
- adding deployment configuration for platforms such as Render or PythonAnywhere.

## Demonstration guide

For the project presentation, a suggested demonstration flow is:

1. Open the landing page.
2. Sign up or log in with an existing demo user.
3. Show the dashboard.
4. Add an income record.
5. Add an expense and upload a receipt.
6. Open the saved expense detail page.
7. Create or open a group.
8. Add a shared group expense.
9. Show settlement status/comments.
10. Open the insights page.
11. Open the leaderboard.
12. Log out.

Before the demonstration, make sure the application is running and the demo database contains enough sample users, expenses, groups, and leaderboard activity to show the main features clearly.

## Repository notes

Generated files such as `__pycache__/`, `.pytest_cache/`, virtual environments, and local environment files should not be committed. The database file should only be committed if the group intentionally wants to provide a prepared demo database.

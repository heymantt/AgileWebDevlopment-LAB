# TrackMint 🌿

TrackMint is a modern, responsive web application designed for group expense tracking, individual income logging, and collaborative debt settlement. Built using the **Flask Application Factory Pattern**, it supports structured database management via SQLAlchemy, stateful and stateless testing protocols, and robust security integrations.

---

## Architecture Overview
---

## Key Features & Business Logic

*   **Unified Expense Dashboard**: Aggregates month-to-date statements, displaying net-to-gross income margins, highest expense shares, and financial alerts.
*   **Split Ledger Protocols**: Facilitates automated database splitting parameters across registered group profiles, maintaining historical integrity for individual split balances.
*   **Gamified Streaks**: Motivates continuous data integrity through dynamic calculations tracking subsequent day entries, adjusting total user ranking metrics inside the leaderboard[cite: 1].
*   **Attachment Repository**: Accommodates digital receipt matching, dynamically binding multi-format files to specific database index arrays[cite: 1].

---

## Database Schema Highlights

The backend operates on a fully relational entity architecture using standard column references[cite: 1]:
*   `users`: Tracks profile configurations, streaks, and gamification points[cite: 1].
*   `groups` & `group_members`: Establishes cascading multi-member operational tables[cite: 1].
*   `receipts`: Stores transaction records, frequencies, and paths to structural files[cite: 1].
*   `expense_splits`: Maps custom fractional balance components down to active group members[cite: 1].
*   `income`: Monitors discrete or continuous cash flow intervals over given date bounds[cite: 1].

---

## Installation & Environment Setup

### 1. Prerequisites
Ensure you have Python 3.10+ installed locally.

### 2. Configure Virtual Environment
```bash
# Initialize shell virtual environment profile
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
# Install Required Framework Add-ons
pip install flask flask-sqlalchemy flask-migrate flask-login flask-wtf email-validator werkzeug
# Initialize Database Schemas & Migrations
flask db upgrade
python app/seed_users.py
# Start Application Platform
python run.py
#Open http://127.0.0.1:5000 in your web browser.
# Verification & Testing Suite
python tests.py
---

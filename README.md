# CarePoint — Hospital Management System

A polished, responsive Flask + SQLite hospital administration demo. Includes dashboard, patient registration/history, doctor directory, appointment scheduling/statuses, billing/payments, global search, login, and dark mode.

## Quick start (Windows / VS Code)

1. Extract the ZIP.
2. Open the **Hospital_Management_System** folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   ```powershell
   python -m venv venv
   ```
5. Activate it in PowerShell:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```
6. Install packages:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Start the app:
   ```powershell
   python app.py
   ```
8. Open **http://127.0.0.1:5000** in your browser.

If PowerShell activation causes trouble, skip activation and run:
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

## Demo login
- Username: `admin`
- Password: `admin123`

Change the demo password and `SECRET_KEY` before any deployment. On first run, SQLite creates `hospital.db` and inserts clearly illustrative sample records. Delete `hospital.db` to reset the local demo database.

## Main features
- Dashboard KPIs, appointment overview, recent patients
- Patient registration, search, profile, appointment history and bills
- Doctor management and availability
- Appointment booking and status updates
- Billing, partial payments, outstanding balance calculations
- Global search across patients, doctors and appointments
- Responsive layout, sidebar navigation, theme toggle, flash notifications

## Important
This is an educational demonstration, not a production clinical system. Sample data is fictional. Do not enter real patient information. A real deployment needs security review, HTTPS, stronger account management, authorization controls, audit logs, backups, privacy compliance, and production configuration. The built-in demo login is not suitable for public hosting.

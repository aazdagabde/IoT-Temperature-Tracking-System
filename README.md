# IoT Project: Temperature and Humidity Monitoring System

## Overview
This project is an Internet of Things (IoT) application designed to monitor temperature and humidity in real time. It provides features such as data visualization, incident management, and alert notifications. The system includes a web dashboard for users to view and manage data, receive notifications, and download incident reports.

---

## Features

### 1. Real-Time Data Monitoring
- Display temperature and humidity data in real-time.
- Visualize data using interactive charts and tables.

### 2. Incident Management
- Detect and log incidents when temperature exceeds predefined thresholds.
- Archive incidents in a database for future reference.
- Implement an escalating alert system to notify users via email if conditions persist.
  
### 3. User Notifications
- Send email alerts to:
  - User 1 immediately when an issue is detected.
  - User 2 if the issue persists for 20 minutes.
  - Admin if the issue continues after 40 minutes.

### 4. Reporting
- Allow users to download incident reports in PDF format.

### 5. User Authentication
- Support user registration and login functionalities.
- Protect sensitive actions using CSRF tokens and secure login mechanisms.

### 6. Dashboard Interface
- Provide a centralized dashboard with:
  - Overview of incidents and alerts.
  - Temperature and humidity trends.
  - Quick access to download reports.

---

## Technologies Used

### Backend
- **Django Framework**: For handling server-side logic and database operations.
- **Django REST Framework**: To expose data as APIs (optional for real-time updates).

### Frontend
- **HTML5**, **CSS3**, **Bootstrap**: For building responsive web interfaces.
- **Chart.js**: For creating interactive charts and visualizations.

### Database
- **SQLite** (default) or **PostgreSQL**: To store user data, incidents, and archived logs.

### Email Notifications
- **SMTP Server**: To send email alerts to users and admins.

### Reporting
- **WeasyPrint**: For generating PDF reports from HTML templates.

---

## Project Structure
```
project-root/
├── DHT/
│   ├── templates/            # HTML templates for frontend views
│   ├── static/               # Static files (CSS, JS, images)
│   ├── views.py              # Backend logic and view functions
│   ├── models.py             # Database models for data storage
│   ├── urls.py               # URL routing configuration
├── manage.py                 # Django management script
├── db.sqlite3                # Default SQLite database
├── requirements.txt          # Python dependencies
```

---

## Installation and Setup

### Prerequisites
- **Python 3.8+** installed.
- A virtual environment tool such as `venv` or `virtualenv`.

### Steps
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd project-root
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Apply database migrations:
   ```bash
   python manage.py migrate
   ```

5. Run the server:
   ```bash
   python manage.py runserver
   ```

6. Access the application at `http://127.0.0.1:8000/` in your web browser.

---

## Usage

### Adding Users
- Register new users via the `/register` page.
- Log in with user credentials to access the dashboard.

### Monitoring Data
- View live temperature and humidity readings on the dashboard.
- Check incident logs for past anomalies.

### Alert System
- Configure the email settings in `settings.py` to enable email notifications.
- Ensure that email credentials and SMTP settings are correctly added.

### Download Reports
- Navigate to the dashboard and click the "Download Report" button to export incident logs as a PDF.

---

## Future Improvements
- Add real-time updates using WebSocket (Django Channels).
- Support more IoT sensors (e.g., air quality, motion detection).
- Enable role-based access control for better security.

---

## Acknowledgments
This project was realized as part of the IoT module at ENSA Oujda, under the supervision of Professor El Moussati Ali. It was developed by:
- **Abdellah Aazdag**
- **Salma Bousslama**

---

## License
This project is licensed under the MIT License. See `LICENSE` file for more details.

---

## Contact
For any queries or suggestions, please contact:
- **Abdellah Aazdag**
- **Salma Bousslama**


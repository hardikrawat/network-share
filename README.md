# Print Express - Shop Management System

A complete SaaS-style web application for print shops. Allows customers to scan a QR code in-shop to upload files directly from their mobile devices, while providing shopkeepers with a powerful, modern command center to manage active orders, maintain a services catalog, and log daily expenses.

## Features

- **Mobile Customer View**: A clean, responsive mobile interface (available in English and Hindi) for customers to easily upload documents and optionally select extra services (like Lamination, Binding, etc.) directly from their phones.
- **Dynamic QR Code**: Generates a local or public QR code automatically for customers to scan and access the upload portal without typing URLs.
- **Command Center Dashboard**: A professional desktop dashboard for shopkeepers to:
  - Track **Active Print Orders** (paginated) with current status updates (Pending, Printing, Completed, Paid).
  - Manage a **Services Catalog** where shopkeepers can add and remove extra services that customers can select.
  - Track **Daily Expenses** (lunch, supplies, etc.).
  - View **Finance Overview** showing Total Revenue (from completed/paid orders) and Total Expenses.
- **Bilingual Support**: Fully supports English and Hindi for both the Customer view and the Command Center.
- **Extensive Test Coverage**: Automated test suite utilizing `pytest` and `playwright` guaranteeing 99%+ backend and frontend reliability.

## Project Structure
```
├── app.py                # Flask application backend
├── templates/
│   └── index.html        # Single Page Application (SPA) frontend
├── static/
│   └── res/              # Assets (favicon, logo, etc.)
├── uploads/              # Local storage for documents and JSON metadata
├── tests/                # Comprehensive test suite (Backend + UI)
├── requirements.txt      # Python dependencies
└── .gitignore            # Git ignore configuration
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. **Install Dependencies**
   Ensure you have Python 3 installed. We recommend setting up a virtual environment.
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the Application**
   Start the Flask backend:
   ```bash
   python3 app.py
   ```
   The application will be accessible at `http://localhost:5005` (or your local IP for mobile access).

4. **Run the Tests (Optional)**
   To run the test suite ensuring your environment is fully functional:
   ```bash
   playwright install chromium
   PYTHONPATH=. pytest --cov=app tests/
   ```

## Workflow Guide

- **Shopkeepers:** Open the web app on your desktop/tablet. You'll see the Command Center. Navigate to the Catalog to configure your offered services and pricing.
- **Customers:** Scan the QR code displayed on the Command Center from their mobile device. They will see a simplified mobile-friendly interface to upload their file and choose options.
- **Order Fulfillment:** The uploaded file immediately appears in the Command Center's Active Print Orders table. The shopkeeper downloads the file, prints it, and updates the status to "Completed" or "Paid".

## Data Storage
This application operates statelessly via lightweight JSON file storage (`metadata.json`, `services.json`, `expenses.json` stored in the `uploads/` directory), ensuring extreme portability and zero database setup. All uploaded files are saved locally to the same directory.
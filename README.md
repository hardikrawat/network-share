# Web App Documentation

## Project Overview
This web application is built using Flask and allows customers to upload files while providing shopkeepers with the ability to view these uploaded files. The application features a simple and intuitive user interface.

## Project Structure
```
webapp/
├── app.py                # Flask application
├── templates/
│   └── index.html        # Main HTML page
├── static/
│   └── css/
│       └── styles.css    # Minimalistic CSS styles
├── uploads/              # Directory for uploaded files
└── requirements.txt      # Flask and dependencies
```

## Setup Instructions

1. **Clone the Repository**
   ```
   git clone <repository-url>
   cd webapp
   ```

2. **Install Dependencies**
   Ensure you have Python 3 and pip installed. Then run:
   ```
   pip install -r requirements.txt
   ```

3. **Run the Application**
   Start the Flask application:
   ```
   python app.py
   ```
   The application will be accessible at `http://0.0.0.0:5000`.

## Usage Guidelines

- **For Customers:**
  - Open the web app in your browser.
  - Select the option to upload a file and submit it.

- **For Shopkeepers:**
  - Access the same URL to view the uploaded files immediately.

## Additional Information
- Ensure the `uploads` directory has the correct permissions for file uploads.
- Modify the `httpd.conf` settings as needed to serve the Flask app through Apache using mod_wsgi.

## License
This project is licensed under the MIT License.
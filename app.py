from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os
import socket

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return 'File uploaded successfully', 201

@app.route('/files', methods=['GET'])
def list_files():
    try:
        files = os.listdir(app.config['UPLOAD_FOLDER'])
        return jsonify(files), 200
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    # Get the local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"App running at http://{local_ip}:5004")
    app.run(host='0.0.0.0', port=5004, debug=True)
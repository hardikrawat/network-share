from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_cors import CORS
import os
import socket
import json
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
UPLOAD_FOLDER = 'uploads'
RES_FOLDER = 'static/res'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RES_FOLDER'] = RES_FOLDER
METADATA_FILE = 'uploads/metadata.json'

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load existing metadata
if os.path.exists(METADATA_FILE):
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
else:
    metadata = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        logger.error('No file part in the request')
        return jsonify({'message': 'No file part', 'status': 'error'}), 400
    file = request.files['file']
    if file.filename == '':
        logger.error('No selected file')
        return jsonify({'message': 'No selected file', 'status': 'error'}), 400
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    logger.info(f'File saved to {file_path}')
    
    # Store metadata
    uploader = request.form.get('uploader', 'Unknown')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    metadata[file.filename] = {'uploader': uploader, 'timestamp': timestamp}
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f)
    logger.info(f'Metadata saved for file {file.filename}')
    
    return jsonify({'message': 'File uploaded successfully', 'status': 'success'}), 201

@app.route('/files', methods=['GET'])
def list_files():
    try:
        files = [{'name': f, 'uploader': metadata[f]['uploader'], 'timestamp': metadata[f]['timestamp']} for f in os.listdir(app.config['UPLOAD_FOLDER']) if f in metadata]
        return jsonify(files), 200
    except Exception as e:
        logger.error(f'Error listing files: {e}')
        return str(e), 500

@app.route('/uploads/<filename>', methods=['GET'])
def get_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        logger.info(f'Serving file: {file_path}')
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        logger.error(f'File not found: {file_path}')
        return 'File not found', 404

@app.route('/res/<filename>', methods=['GET'])
def get_res_file(filename):
    file_path = os.path.join(app.config['RES_FOLDER'], filename)
    if os.path.exists(file_path):
        logger.info(f'Serving file: {file_path}')
        return send_from_directory(app.config['RES_FOLDER'], filename)
    else:
        logger.error(f'File not found at: {file_path}')
        return f'File not found at: {file_path}', 404

if __name__ == '__main__':
    # Get the local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"App running at http://{local_ip}:5005")
    app.run(host='0.0.0.0', port=5005, debug=True)
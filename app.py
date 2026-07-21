from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_cors import CORS
import os
import socket
import json
import logging
import uuid
import webbrowser
from threading import Timer
from datetime import datetime
from pyngrok import ngrok

app = Flask(__name__)
CORS(app)

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

UPLOAD_FOLDER = 'uploads'
RES_FOLDER = 'static/res'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RES_FOLDER'] = RES_FOLDER
METADATA_FILE = 'uploads/metadata.json'
SERVICES_FILE = 'uploads/services.json'
EXPENSES_FILE = 'uploads/expenses.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RES_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_json(filepath, default):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            try:
                return json.load(f)
            except:
                return default
    return default

def save_json(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f)

metadata = load_json(METADATA_FILE, {})
services = load_json(SERVICES_FILE, [
    {"id": str(uuid.uuid4()), "name": "A4 Black & White", "price": 0.10},
    {"id": str(uuid.uuid4()), "name": "A4 Color Print", "price": 0.50},
    {"id": str(uuid.uuid4()), "name": "Lamination", "price": 1.00}
])
expenses = load_json(EXPENSES_FILE, [])

@app.route('/')
def index():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    
    public_url = os.environ.get("NGROK_PUBLIC_URL", "")
    return render_template('index.html', local_ip=local_ip, public_url=public_url)

@app.route('/api/services', methods=['GET', 'POST'])
def handle_services():
    global services
    if request.method == 'GET':
        return jsonify(services)
    elif request.method == 'POST':
        data = request.json
        if 'id' in data: # update
            for i, s in enumerate(services):
                if s['id'] == data['id']:
                    services[i] = data
                    break
        else: # add new
            data['id'] = str(uuid.uuid4())
            services.append(data)
        save_json(SERVICES_FILE, services)
        return jsonify({'status': 'success', 'service': data})

@app.route('/api/services/<service_id>', methods=['DELETE'])
def delete_service(service_id):
    global services
    services = [s for s in services if s['id'] != service_id]
    save_json(SERVICES_FILE, services)
    return jsonify({'status': 'success'})

@app.route('/api/expenses', methods=['GET', 'POST'])
def handle_expenses():
    global expenses
    if request.method == 'GET':
        return jsonify(expenses)
    elif request.method == 'POST':
        data = request.json
        data['id'] = str(uuid.uuid4())
        data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        expenses.append(data)
        save_json(EXPENSES_FILE, expenses)
        return jsonify({'status': 'success', 'expense': data})

@app.route('/api/expenses/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    global expenses
    expenses = [e for e in expenses if e['id'] != expense_id]
    save_json(EXPENSES_FILE, expenses)
    return jsonify({'status': 'success'})

@app.route('/api/finance', methods=['GET'])
def get_finance():
    total_revenue = 0
    for order in metadata.values():
        if order.get('status') in ['Paid', 'Completed']:
            total_revenue += float(order.get('total_price', 0))
    
    total_expenses = sum(float(e.get('amount', 0)) for e in expenses)
    
    return jsonify({
        'revenue': total_revenue,
        'expenses': total_expenses,
        'profit': total_revenue - total_expenses
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part', 'status': 'error'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file', 'status': 'error'}), 400
        
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    uploader = request.form.get('uploader', 'Unknown')
    selected_services_raw = request.form.get('services', '[]')
    try:
        selected_services = json.loads(selected_services_raw)
    except:
        selected_services = []
        
    total_price = 0
    for ss in selected_services:
        qty = int(ss.get('qty', 1))
        price = float(ss.get('price', 0))
        total_price += qty * price

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    order_id = str(uuid.uuid4())
    
    # Capture device information
    user_agent = request.user_agent
    device_info = {
        'ip': request.remote_addr,
        'platform': user_agent.platform if user_agent.platform else 'Unknown',
        'browser': user_agent.browser if user_agent.browser else 'Unknown',
        'raw_ua': user_agent.string
    }
    
    metadata[order_id] = {
        'order_id': order_id,
        'filename': file.filename,
        'uploader': uploader,
        'timestamp': timestamp,
        'services': selected_services,
        'total_price': total_price,
        'status': 'Pending',
        'device': device_info
    }
    save_json(METADATA_FILE, metadata)
    
    return jsonify({'message': 'File uploaded successfully', 'status': 'success'}), 201

@app.route('/api/orders', methods=['GET'])
def get_orders():
    # Return list of orders sorted by timestamp descending
    orders_list = []
    for k, v in metadata.items():
        # Ensure older items without 'order_id' or 'filename' in their dict use the key
        item = v.copy()
        item['order_id'] = item.get('order_id', k)
        item['filename'] = item.get('filename', k)
        orders_list.append(item)
        
    orders_list.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    return jsonify(orders_list)

@app.route('/api/orders/<order_id>', methods=['PATCH', 'DELETE'])
def update_order(order_id):
    global metadata
    if order_id not in metadata:
        return jsonify({'status': 'error', 'message': 'Not found'}), 404
        
    if request.method == 'DELETE':
        filename = metadata[order_id].get('filename', order_id)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        del metadata[order_id]
        save_json(METADATA_FILE, metadata)
        return jsonify({'status': 'success'})
        
    elif request.method == 'PATCH':
        data = request.json
        if 'status' in data:
            metadata[order_id]['status'] = data['status']
        save_json(METADATA_FILE, metadata)
        return jsonify({'status': 'success'})

@app.route('/uploads/<filename>', methods=['GET'])
def get_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/res/<filename>', methods=['GET'])
def get_res_file(filename):
    return send_from_directory(app.config['RES_FOLDER'], filename)

if __name__ == '__main__': # pragma: no cover
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"App running at http://{local_ip}:5005")
    
    try:
        if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
            auth_token = os.environ.get("NGROK_AUTH_TOKEN")
            if auth_token:
                ngrok.set_auth_token(auth_token)
            tunnel = ngrok.connect(5005)
            print(f"[*] Ngrok Tunnel URL: {tunnel.public_url}")
            os.environ["NGROK_PUBLIC_URL"] = tunnel.public_url
    except Exception as e:
        print(f"[*] Ngrok error: {e}")
        
    def open_browser():
        webbrowser.open(f"http://127.0.0.1:5005")
        
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        Timer(1.5, open_browser).start()
        
    app.run(host='0.0.0.0', port=5005, debug=True)
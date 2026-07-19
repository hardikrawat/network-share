import os
import json
import pytest
from io import BytesIO
from unittest.mock import patch

# Configure the app for testing before importing it
import app as myapp

@pytest.fixture
def client(tmp_path):
    # Set up a temporary directory for uploads and files
    myapp.app.config['TESTING'] = True
    myapp.app.config['UPLOAD_FOLDER'] = str(tmp_path)
    
    # Mock file paths
    myapp.METADATA_FILE = str(tmp_path / "metadata.json")
    myapp.SERVICES_FILE = str(tmp_path / "services.json")
    myapp.EXPENSES_FILE = str(tmp_path / "expenses.json")
    
    # Reset in-memory data
    myapp.metadata = {}
    myapp.services = [
        {"id": "test-svc", "name": "Test Service", "price": 10.0}
    ]
    myapp.expenses = []
    
    with myapp.app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Print Shop System' in response.data or b'Print Express' in response.data

def test_get_services(client):
    res = client.get('/api/services')
    assert res.status_code == 200
    data = res.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'Test Service'

def test_add_service(client):
    res = client.post('/api/services', json={"name": "New Service", "price": 5.0})
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'success'
    assert 'id' in data['service']
    
    # Check if added
    res2 = client.get('/api/services')
    assert len(res2.get_json()) == 2

def test_update_service(client):
    res = client.post('/api/services', json={"id": "test-svc", "name": "Updated Svc", "price": 12.0})
    assert res.status_code == 200
    
    res2 = client.get('/api/services')
    data = res2.get_json()
    assert data[0]['name'] == 'Updated Svc'
    assert data[0]['price'] == 12.0

def test_delete_service(client):
    res = client.delete('/api/services/test-svc')
    assert res.status_code == 200
    
    res2 = client.get('/api/services')
    assert len(res2.get_json()) == 0

def test_add_expense(client):
    res = client.post('/api/expenses', json={"description": "Paper", "amount": 100})
    assert res.status_code == 200
    
    res2 = client.get('/api/expenses')
    data = res2.get_json()
    assert len(data) == 1
    assert data[0]['description'] == 'Paper'

def test_delete_expense(client):
    res = client.post('/api/expenses', json={"description": "Ink", "amount": 50})
    exp_id = res.get_json()['expense']['id']
    
    res2 = client.delete(f'/api/expenses/{exp_id}')
    assert res2.status_code == 200
    
    res3 = client.get('/api/expenses')
    assert len(res3.get_json()) == 0

def test_upload_file(client):
    data = {
        'uploader': 'TestUser',
        'services': json.dumps([{"name": "Test Service", "price": 10, "qty": 2}]),
        'file': (BytesIO(b"my file contents"), 'test_image.jpg')
    }
    res = client.post('/upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 201
    assert res.get_json()['status'] == 'success'
    
    # Check if order was created
    res2 = client.get('/api/orders')
    orders = res2.get_json()
    assert len(orders) == 1
    assert orders[0]['filename'] == 'test_image.jpg'
    assert orders[0]['total_price'] == 20.0
    assert orders[0]['status'] == 'Pending'
    
    return orders[0]['order_id']

def test_upload_no_file(client):
    res = client.post('/upload', data={})
    assert res.status_code == 400

def test_upload_empty_file(client):
    data = {'file': (BytesIO(b""), '')}
    res = client.post('/upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 400

def test_update_order(client):
    order_id = test_upload_file(client)
    
    res = client.patch(f'/api/orders/{order_id}', json={"status": "Completed"})
    assert res.status_code == 200
    
    orders = client.get('/api/orders').get_json()
    assert orders[0]['status'] == 'Completed'

def test_update_order_not_found(client):
    res = client.patch('/api/orders/invalid-id', json={"status": "Completed"})
    assert res.status_code == 404

def test_delete_order(client):
    order_id = test_upload_file(client)
    
    res = client.delete(f'/api/orders/{order_id}')
    assert res.status_code == 200
    
    orders = client.get('/api/orders').get_json()
    assert len(orders) == 0

def test_finance(client):
    test_upload_file(client) # creates an order (20.0 price, pending)
    
    # Add expense (10.0)
    client.post('/api/expenses', json={"description": "Paper", "amount": 10.0})
    
    res = client.get('/api/finance')
    data = res.get_json()
    # Pending order is not revenue
    assert data['revenue'] == 0
    assert data['expenses'] == 10.0
    
    # Mark order as paid
    orders = client.get('/api/orders').get_json()
    client.patch(f"/api/orders/{orders[0]['order_id']}", json={"status": "Paid"})
    
    res2 = client.get('/api/finance')
    data2 = res2.get_json()
    assert data2['revenue'] == 20.0
    assert data2['profit'] == 10.0

def test_serve_files(client):
    order_id = test_upload_file(client)
    orders = client.get('/api/orders').get_json()
    filename = orders[0]['filename']
    
    res = client.get(f'/uploads/{filename}')
    assert res.status_code == 200
    assert res.data == b"my file contents"

def test_serve_res_file(client, tmp_path):
    res_dir = tmp_path / "static" / "res"
    res_dir.mkdir(parents=True, exist_ok=True)
    test_file = res_dir / "test.jpg"
    test_file.write_bytes(b"image data")
    
    myapp.app.config['RES_FOLDER'] = str(res_dir)
    
    res = client.get('/res/test.jpg')
    assert res.status_code == 200
    assert res.data == b"image data"

def test_load_json_invalid(tmp_path):
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid_json}")
    assert myapp.load_json(str(invalid_file), {"default": True}) == {"default": True}

def test_index_socket_error(client):
    with patch('socket.socket') as mock_sock:
        mock_sock.return_value.connect.side_effect = Exception("Mock Error")
        res = client.get('/')
        assert res.status_code == 200

def test_upload_invalid_services(client):
    data = {
        'uploader': 'TestUser',
        'services': '{invalid json',
        'file': (BytesIO(b"my file contents"), 'test_image.jpg')
    }
    res = client.post('/upload', data=data, content_type='multipart/form-data')
    assert res.status_code == 201

def test_delete_order_oserror(client, tmp_path):
    # Upload first
    data = {
        'uploader': 'TestUser',
        'services': '[]',
        'file': (BytesIO(b"my file contents"), 'test_image_delete.jpg')
    }
    client.post('/upload', data=data, content_type='multipart/form-data')
    
    orders = client.get('/api/orders').get_json()
    order_id = orders[0]['order_id']
    filename = orders[0]['filename']
    
    # manually delete file to trigger OSError on server
    os.remove(str(tmp_path / filename))
    
    res = client.delete(f'/api/orders/{order_id}')
    assert res.status_code == 200

import os
import pytest
import subprocess
import time
import socket
from playwright.sync_api import Page, expect

TEST_PORT = 5010
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

@pytest.fixture(scope="session", autouse=True)
def start_server(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("uploads")
    
    # Create a wrapper script
    script_content = f"""
import os
os.environ['WERKZEUG_RUN_MAIN'] = 'true' # disable browser auto-open
import app as myapp

myapp.app.config['TESTING'] = True
myapp.app.config['UPLOAD_FOLDER'] = r'{str(tmp_dir)}'
myapp.METADATA_FILE = r'{str(tmp_dir / "metadata.json")}'
myapp.SERVICES_FILE = r'{str(tmp_dir / "services.json")}'
myapp.EXPENSES_FILE = r'{str(tmp_dir / "expenses.json")}'

myapp.services = [
    {{"id": "test-svc", "name": "UI Test Service", "price": 10.0}}
]
myapp.metadata = {{}}
myapp.expenses = []

myapp.app.run(host='127.0.0.1', port={TEST_PORT}, debug=False)
"""
    wrapper_path = tmp_dir / "run_wrapper.py"
    wrapper_path.write_text(script_content)
    
    # Run the wrapper
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    proc = subprocess.Popen(["python3", str(wrapper_path)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for server
    started = False
    for _ in range(20):
        try:
            with socket.create_connection(('127.0.0.1', TEST_PORT), timeout=0.5):
                started = True
                break
        except OSError:
            time.sleep(0.5)
            
    if not started:
        proc.kill()
        out, err = proc.communicate()
        raise RuntimeError(f"Server failed to start:\\nSTDOUT: {out.decode()}\\nSTDERR: {err.decode()}")
        
    yield
    
    proc.terminate()
    proc.wait()

def test_dashboard_loads(page: Page):
    page.goto(BASE_URL)
    expect(page.locator("h1").first).to_contain_text("Print Express")

def test_add_service(page: Page):
    page.goto(BASE_URL)
    # Switch to catalog tab
    page.click("div.nav-item:has-text('Catalog')")
    
    # Fill in the form
    page.fill("#service-name", "Playwright Print")
    page.fill("#service-price", "5.50")
    
    # Submit
    page.click("#service-submit-btn")
    
    # Verify toast
    expect(page.locator("#toast")).to_be_visible()
    
    # Verify it appears in table
    expect(page.locator("#services-table-body")).to_contain_text("Playwright Print")

def test_place_order(page: Page):
    page.goto(BASE_URL)
    
    with open("test_upload.txt", "w") as f:
        f.write("Hello World")
        
    page.locator("#cust-file").set_input_files("test_upload.txt")
    
    # Select a service (click the checkbox div)
    page.wait_for_selector(".service-checkbox")
    
    # Click the first service
    page.click(".service-checkbox")
    
    # Submit order
    page.on("dialog", lambda dialog: dialog.accept()) # accept alert
    page.click("button:has-text('Submit Order')")
    
    # Clean up dummy file
    os.remove("test_upload.txt")
    
    # After submission, it reloads. Navigate to Command Center
    page.goto(BASE_URL)
    page.click("div.nav-item:has-text('Orders')")
    
    # Verify order is in table
    expect(page.locator("#orders-table-body")).to_contain_text("test_upload.txt")
    
def test_update_order(page: Page):
    page.goto(BASE_URL)
    page.click("div.nav-item:has-text('Orders')")
    
    # Find the select and change status to 'Completed'
    select = page.locator("select.neo-select").first
    select.select_option("Completed")
    
    # Verify status changed visually
    expect(page.locator("span.neo-badge", has_text="Completed")).to_be_visible()

def test_delete_order(page: Page):
    page.goto(BASE_URL)
    page.click("div.nav-item:has-text('Orders')")
    
    # Count rows before
    rows_before = page.locator("#orders-table-body tr").count()
    
    # Click delete
    page.click("button.magenta:has-text('Del')")
    
    # It might take a moment to fetch and re-render
    time.sleep(1)
    
    # Verify row count decreased or table is empty
    rows_after = page.locator("#orders-table-body tr").count()
    assert rows_after < rows_before
    
def test_add_expense(page: Page):
    page.goto(BASE_URL)
    page.click("div.nav-item:has-text('Expenses')")
    
    page.fill("#exp-desc", "Lunch")
    page.fill("#exp-amount", "250")
    page.click("button:has-text('Log Expense')")
    
    # Verify it appears
    expect(page.locator("#expenses-table-body")).to_contain_text("Lunch")

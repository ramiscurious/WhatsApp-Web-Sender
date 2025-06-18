import os
import time
import urllib.parse
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

app = Flask(__name__)

# Configuration
CONFIG = {
    'SESSION_DIR': os.path.join(os.getcwd(), 'whatsapp_session'),
    'QR_SCAN_TIMEOUT': 45,
    'MESSAGE_TIMEOUT': 15,
    'MAX_CONTACTS': 100,
    'MIN_DELAY': 2,
    'MAX_DELAY': 60,
    'MAX_MESSAGE_LENGTH': 4096
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_sender.log'),
        logging.StreamHandler()
    ]
)

def prepare_message(message):
    """Handle multi-line messages and preserve formatting for WhatsApp"""
    # Normalize line endings and encode for WhatsApp URL
    return message.replace('\r\n', '\n').replace('\n', '%0A')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send_messages():
    start_time = time.time()
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        contacts = data.get("contacts", [])
        message = data.get("message", "").strip()
        delay = int(data.get("delay", 5))

        # Validate inputs
        if not contacts:
            return jsonify({"error": "No contacts provided"}), 400
        if len(contacts) > CONFIG['MAX_CONTACTS']:
            return jsonify({"error": f"Maximum {CONFIG['MAX_CONTACTS']} contacts allowed per request"}), 400
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
        if len(message) > CONFIG['MAX_MESSAGE_LENGTH']:
            return jsonify({"error": f"Message too long (max {CONFIG['MAX_MESSAGE_LENGTH']} characters)"}), 400
        if delay < CONFIG['MIN_DELAY'] or delay > CONFIG['MAX_DELAY']:
            return jsonify({"error": f"Delay must be between {CONFIG['MIN_DELAY']}-{CONFIG['MAX_DELAY']} seconds"}), 400
        if '\x00' in message:
            return jsonify({"error": "Message contains null bytes"}), 400

        # Initialize Chrome Driver
        try:
            options = webdriver.ChromeOptions()
            options.add_argument(f"--user-data-dir={CONFIG['SESSION_DIR']}")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.implicitly_wait(10)
        except Exception as e:
            logging.error(f"Driver initialization failed: {str(e)}")
            return jsonify({"error": f"Browser setup failed: {str(e)}"}), 500

        results = []
        try:
            # Load WhatsApp Web
            driver.get("https://web.whatsapp.com")
            logging.info("Waiting for WhatsApp Web to load...")

            # Wait for login
            try:
                WebDriverWait(driver, CONFIG['QR_SCAN_TIMEOUT']).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@title="Chats"]'))
                )
                logging.info("WhatsApp Web loaded successfully")
            except TimeoutException:
                driver.save_screenshot('login_timeout.png')
                logging.error("WhatsApp login timeout")
                return jsonify({
                    "error": "Login timeout",
                    "solution": "1. Scan QR code manually first\n2. Ensure stable internet connection",
                    "screenshot": "login_timeout.png"
                }), 408

            # Process contacts
            for contact in contacts:
                contact_number = contact.get("number", "").strip()
                contact_name = contact.get("name", "").strip()
                
                if not contact_number:
                    results.append({
                        "number": "MISSING",
                        "name": contact_name,
                        "status": "failed",
                        "error": "Phone number missing"
                    })
                    continue

                try:
                    # Personalize message and handle multi-line/emoji
                    personalized_msg = message.replace("{name}", contact_name)
                    prepared_msg = prepare_message(personalized_msg)
                    chat_url = f"https://web.whatsapp.com/send?phone={contact_number}&text={prepared_msg}"
                    
                    # Open chat
                    driver.get(chat_url)
                    logging.info(f"Opening chat with {contact_number}")

                    # Wait and send message
                    try:
                        send_btn = WebDriverWait(driver, CONFIG['MESSAGE_TIMEOUT']).until(
                            EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                        )
                        send_btn.click()
                        logging.info(f"Message sent to {contact_number}")
                        
                        results.append({
                            "number": contact_number,
                            "name": contact_name,
                            "status": "sent",
                            "message": personalized_msg
                        })
                    except (TimeoutException, NoSuchElementException):
                        driver.save_screenshot(f'send_error_{contact_number}.png')
                        results.append({
                            "number": contact_number,
                            "name": contact_name,
                            "status": "failed",
                            "error": "Send button not found",
                            "screenshot": f'send_error_{contact_number}.png'
                        })
                        continue

                    # Delay between messages
                    time.sleep(delay)

                except Exception as e:
                    logging.error(f"Error with {contact_number}: {str(e)}")
                    results.append({
                        "number": contact_number,
                        "name": contact_name,
                        "status": "failed",
                        "error": str(e)
                    })

        finally:
            driver.quit()
            logging.info(f"Process completed in {time.time() - start_time:.2f} seconds")

        return jsonify({
            "success": True,
            "sent": len([r for r in results if r['status'] == 'sent']),
            "failed": len([r for r in results if r['status'] == 'failed']),
            "results": results
        })

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Unexpected server error",
            "details": str(e),
            "solution": "Check logs and try again"
        }), 500

if __name__ == '__main__':
    if not os.path.exists(CONFIG['SESSION_DIR']):
        os.makedirs(CONFIG['SESSION_DIR'])
    app.run(debug=True, host='0.0.0.0', port=5000)
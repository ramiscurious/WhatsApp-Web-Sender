WhatsApp Web Sender

A Python-based tool for automating WhatsApp Web messages using Selenium and a simple HTML interface.

Features :
Send bulk or single messages via WhatsApp Web.
User-friendly frontend with index.html .
Custom Chrome session handling for login persistence.
Logs messaging activity to whatsapp_sender.log .
Cross-platform execution using app.py and run_app.bat .

Tech Stack :
Python
Flask
Selenium WebDriver
HTML, CSS

Folder Structure :
whatsapp-web-sender/
├── app.py # Main Flask app
├── chromedriver.exe # Chrome driver for Selenium (Windows)
├── start.html # Launch page
├── run_app.bat # Batch file to run the app (Windows)
├── requirements.txt # Python dependencies
├── templates/index.html # Frontend interface
├── static/styles.css # CSS styles
├── whatsapp_session/ # Chrome session data
└── whatsapp_sender.log # Log file


How to Use :
Clone the repo:
   git clone https://github.com/your-username/whatsapp-web-sender.git
   cd whatsapp-web-sender

Install dependencies:
  pip install -r requirements.txt

Run the app:
  python app.py

Open your browser at http://localhost:5000

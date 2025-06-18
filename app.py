# AI Health Assistant for Seniors (Backend + Deployment Ready)
# Deployment Instructions (Render or Replit)
# 1. Create a GitHub repository and add this file.
# 2. Add a requirements.txt file with required packages.
# 3. Deploy to Render (free tier works). Add environment variables in settings.
# 4. Use POST requests to /create_reminder and /ask endpoints to interact.

from flask import Flask, request, jsonify
import openai
import sqlite3
import time
import threading
from twilio.rest import Client
import os

app = Flask(__name__)

# STEP 1: Set Your API Keys from Environment Variables
openai.api_key = os.environ.get('OPENAI_API_KEY')
twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_phone = os.environ.get('TWILIO_PHONE')
client = Client(twilio_sid, twilio_token)

# STEP 2: Initialize Local SQLite Database
conn = sqlite3.connect('senior_health.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, message TEXT, time TEXT)''')
conn.commit()

# STEP 3: Define Helper to Send Reminder via SMS
def send_reminder(name, phone, message):
    try:
        client.messages.create(
            body=f"Hi {name}, just a reminder: {message}",
            from_=twilio_phone,
            to=phone
        )
    except Exception as e:
        print(f"Error sending reminder: {e}")

# STEP 4: Route to Accept Reminder Requests
@app.route('/create_reminder', methods=['POST'])
def create_reminder():
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        message = data.get('message')
        time_str = data.get('time')

        if not all([name, phone, message, time_str]):
            return jsonify({'error': 'Missing required fields'}), 400

        c.execute("INSERT INTO reminders (name, phone, message, time) VALUES (?, ?, ?, ?)",
                  (name, phone, message, time_str))
        conn.commit()
        return jsonify({'status': 'Reminder created successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# STEP 5: Background Thread to Check Reminders
def reminder_checker():
    while True:
        try:
            c.execute("SELECT * FROM reminders")
            rows = c.fetchall()
            current_time = time.strftime("%H:%M")
            for row in rows:
                if row[4] == current_time:
                    send_reminder(row[1], row[2], row[3])
            time.sleep(60)  # check every minute
        except Exception as e:
            print(f"Error checking reminders: {e}")

threading.Thread(target=reminder_checker, daemon=True).start()

# STEP 6: Chatbot Endpoint to Answer Health Questions
@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful health assistant for seniors."},
                {"role": "user", "content": prompt}
            ]
        )
        return jsonify({'response': response['choices'][0]['message']['content']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# STEP 7: Start the Flask Server
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

# AI Health Assistant for Seniors (Prototype - Backend Focus)
# Instructions to Apply and Run the App:
# 1. Replace API keys with real ones
# 2. Install dependencies using pip: flask, openai, twilio, schedule
# 3. Run this file with Python to launch the local server

from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import sqlite3
import time
import os
import threading
from twilio.rest import Client

app = Flask(__name__)
CORS(app)

# STEP 1: Set Your API Keys
openai.api_key = os.getenv('OPENAI_API_KEY')
twilio_sid = os.getenv('twilio_sid')
twilio_token = os.getenv('twilio_token')
twilio_phone = os.getenv('twilio_phone')
client = Client(twilio_sid, twilio_token)

# STEP 2: Initialize Local SQLite Database
conn = sqlite3.connect('senior_health.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS reminders (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, message TEXT, time TEXT)''')
conn.commit()

# STEP 3: Define Helper to Send Reminder via SMS
def send_reminder(name, phone, message):
    client.messages.create(
        body=f"Hi {name}, just a reminder: {message}",
        from_=twilio_phone,
        to=phone
    )

# STEP 4: Route to Accept Reminder Requests
@app.route('/create_reminder', methods=['POST'])
def create_reminder():
    data = request.json
    name = data['name']
    phone = data['phone']
    message = data['message']
    time_str = data['time']
    c.execute("INSERT INTO reminders (name, phone, message, time) VALUES (?, ?, ?, ?)", (name, phone, message, time_str))
    conn.commit()
    return jsonify({'status': 'Reminder created successfully'})

# NEW: Instant Reminder Endpoint
@app.route('/send_now', methods=['POST'])
def send_now():
    data = request.json
    name = data['name']
    phone = data['phone']
    message = data['message']
    try:
        send_reminder(name, phone, message)
        return jsonify({'status': 'Reminder sent instantly'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# STEP 5: Background Thread to Check Reminders
def reminder_checker():
    while True:
        c.execute("SELECT * FROM reminders")
        rows = c.fetchall()
        current_time = time.strftime("%H:%M")
        for row in rows:
            if row[4] == current_time:
                send_reminder(row[1], row[2], row[3])
        time.sleep(60)  # check every minute

threading.Thread(target=reminder_checker, daemon=True).start()

# STEP 6: Chatbot Endpoint to Answer Health Questions
@app.route('/send_now', methods=['GET', 'POST'])
def ask():
    data = request.json
    prompt = data['prompt']
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful health assistant for seniors."},
            {"role": "user", "content": prompt}
        ]
    )
    return jsonify({'response': response['choices'][0]['message']['content']})

# STEP 7: Start the Flask Server
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")



      

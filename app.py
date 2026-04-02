import os
import sqlite3
from flask import Flask, request, jsonify, render_template, redirect, session
import whisper

app = Flask(__name__)
app.secret_key = "secret123"

model = whisper.load_model("base")

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ---------------- #
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        transcript TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            print("✅ LOGIN SUCCESS")
            session['user_id'] = user[0]
            return redirect('/dashboard')
        else:
           print("❌ LOGIN FAILED")

    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("dashboard.html")

@app.route('/upload', methods=['POST'])
def upload_audio():
    try:
        file = request.files['file']

        if not file:
            return jsonify({"text": "No file uploaded ❌"})

        filepath = os.path.join("uploads", file.filename)
        file.save(filepath)

        print("📁 File saved:", filepath)

        # Transcribe
        result = model.transcribe(
        filepath,
        fp16=False,  # CPU safe
        temperature=0.0,  # more accurate
        best_of=5,
        beam_size=5,
        condition_on_previous_text=True,
        initial_prompt="This is a detailed medical conversation between a doctor and a patient. Use accurate medical terminology."
)

        text = result["text"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("INSERT INTO history (user_id, transcript) VALUES (?, ?)",
               (session['user_id'], text))

        conn.commit()
        conn.close()

        print("🧠 TRANSCRIPTION:", text)

        return jsonify({"text": text})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"text": "Error occurred: " + str(e)})
def register():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            error = "User already exists ❌"
        else:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect('/login')

        conn.close()

    return render_template("register.html", error=error)

@app.route('/history')
def get_history():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transcript 
        FROM history 
        WHERE user_id=? 
        ORDER BY id DESC 
        LIMIT 5
    """, (session['user_id'],))

    data = cursor.fetchall()
    conn.close()

    return jsonify(data)

@app.route('/history-page')
def history_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("history.html")

@app.route('/clear-history', methods=['POST'])
def clear_history():
    print("🔥 CLEAR HISTORY CALLED")

    if 'user_id' not in session:
        print("❌ NO SESSION")
        return jsonify({"error": "Not logged in"})

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    print("USER ID:", session['user_id'])

    cursor.execute("DELETE FROM history WHERE user_id=?", (session['user_id'],))

    conn.commit()
    conn.close()

    print("✅ HISTORY CLEARED")

    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=False)
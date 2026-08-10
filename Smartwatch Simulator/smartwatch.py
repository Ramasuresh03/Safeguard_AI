from flask import Flask, render_template, jsonify
import random, threading, time, requests
from datetime import datetime

app = Flask(__name__)

DASHBOARD_API = "http://127.0.0.1:5000/receive-data"
latest_data = {}

# ================= GENERATE DATA =================
def generate_data():
    global latest_data

    heart_rate = random.randint(60,110)
    sys = random.randint(110,135)
    dia = random.randint(70,90)
    spo2 = random.randint(94,100)

    # stress numeric
    if heart_rate > 100 or spo2 < 95:
        stress = 2
    elif heart_rate > 85:
        stress = 1
    else:
        stress = 0

    # -------- anomaly simulation ----------
    if random.random() < 0.15:
        heart_rate = random.randint(120,160)
        spo2 = random.randint(85,93)
        stress = 2

    latest_data = {
        "heart_rate": heart_rate,
        "bp": f"{sys}/{dia}",
        "spo2": spo2,
        "stress": stress,
        "time": datetime.now().strftime("%H:%M:%S")
    }

    return latest_data


# ================= PUSH TO DASHBOARD =================
def send_to_dashboard():
    while True:
        data = generate_data()
        try:
            requests.post(DASHBOARD_API, json=data, timeout=2)
            print("Sent:", data)
        except:
            print("Dashboard not reachable")

        time.sleep(5)


# ================= ROUTES =================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")



@app.route("/data")
def data():
    return jsonify(generate_data())


threading.Thread(target=send_to_dashboard, daemon=True).start()

if __name__ == "__main__":
    app.run(debug=True, port=5001)

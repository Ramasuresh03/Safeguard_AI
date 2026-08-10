import re
from flask import Flask, render_template, jsonify, request
import joblib
import pandas as pd
from twilio.rest import Client

app = Flask(__name__)

# LOAD MODEL
model = joblib.load("women_safety_model.pkl")

# ── Twilio credentials ──────────────────────────────────
ACCOUNT_SID   = ""          # ← your Twilio Account SID
AUTH_TOKEN    = ""           # ← your Twilio Auth Token
TWILIO_NUMBER = ""           # ← your Twilio number  e.g. +1XXXXXXXXXX

# ── In-memory store ─────────────────────────────────────────
latest_data = {}
pending_sms = False          # True between Emergency detection and GPS push

guardian = {
    "name":  "",
    "phone": "",             # stored in E.164, e.g. +919876543210
}

# ── Helpers ─────────────────────────────────────────────────
def normalise_phone(phone: str) -> str:
    """
    Auto-add +91 for bare 10-digit Indian numbers.
    Strips spaces/dashes so Twilio always gets clean E.164.
    """
    digits = re.sub(r"[\s\-().+]", "", phone)
    if len(digits) == 10 and digits[0] in "6789":
        return "+91" + digits          # Indian mobile without country code
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return "+" + digits            # 919XXXXXXXXX → +919XXXXXXXXX
    # Already has a leading +
    if phone.strip().startswith("+"):
        return "+" + digits
    return phone.strip()


def send_sms(msg: str, to: str = None) -> bool:
    """Send SMS via Twilio. Returns True on success, False on failure."""
    target = to or guardian["phone"]
    if not target:
        print("SMS SKIPPED — no guardian phone set. Add a guardian first.")
        return False
    if not ACCOUNT_SID or not AUTH_TOKEN or not TWILIO_NUMBER:
        print("SMS SKIPPED — Twilio credentials not configured in app.py.")
        return False

    # Normalise to E.164
    target = normalise_phone(target)

    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        message = client.messages.create(
            body=msg,
            from_=TWILIO_NUMBER,
            to=target
        )
        print(f"✅ SMS SENT → {guardian['name'] or target}  SID={message.sid}")
        return True
    except Exception as e:
        print(f"❌ SMS ERROR: {e}")
        return False


# ====================================================================
# PAGES
# ====================================================================
@app.route("/")
def index(): return render_template("index.html")

@app.route("/home")
def home(): return render_template("home.html")

@app.route("/about")
def about(): return render_template("about.html")

@app.route("/team")
def team(): return render_template("team.html")

@app.route("/future")
def future(): return render_template("future.html")


# ====================================================================
# GUARDIAN  —  GET returns current, POST saves new
# ====================================================================
@app.route("/guardian", methods=["GET", "POST"])
def guardian_endpoint():
    global guardian

    if request.method == "GET":
        return jsonify({"name": guardian["name"], "phone": guardian["phone"]})

    data  = request.json or {}
    name  = str(data.get("name",  "")).strip()
    phone = str(data.get("phone", "")).strip()

    if not name:
        return jsonify({"status": "error", "error": "Guardian name is required."}), 400
    if not phone:
        return jsonify({"status": "error", "error": "Phone number is required."}), 400

    # Accept bare digits — normalise later
    digits = re.sub(r"[\s\-().+]", "", phone)
    if not re.match(r"^\d{7,15}$", digits):
        return jsonify({"status": "error",
                        "error": "Enter a valid phone number (e.g. 9876543210 or +919876543210)."}), 400

    guardian["name"]  = name
    guardian["phone"] = normalise_phone(phone)

    print(f"GUARDIAN SET → Name: {name}  Phone: {guardian['phone']}")

    # Confirmation SMS to the guardian
    ok = send_sms(
        f"✅ Hi {name}!\n"
        f"You have been added as the Emergency Guardian in SafeGuard Women Safety System.\n"
        f"You will receive an SMS with GPS location whenever an emergency is detected.\n"
        f"— SafeGuard System",
        to=guardian["phone"]
    )

    return jsonify({
        "status": "saved",
        "name":   name,
        "phone":  guardian["phone"],
        "sms_sent": ok
    })


# ====================================================================
# RECEIVE DATA  (from wearable / test script)
# ====================================================================
@app.route("/receive-data", methods=["POST"])
def receive_data():
    global latest_data, pending_sms

    data = request.json or {}
    try:
        hr          = int(data["heart_rate"])
        sys_bp, dia = map(int, data["bp"].split("/"))
        spo2        = int(data["spo2"])
        stress      = int(data["stress"])
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    features = pd.DataFrame(
        [[hr, sys_bp, dia, spo2, stress]],
        columns=["HeartRate", "Sys", "Dia", "SpO2", "Stress"]
    )
    prediction  = model.predict(features)[0]
    risk_map    = {0: ("Safe", 30), 1: ("Warning", 70), 2: ("Emergency", 95)}
    risk_text, risk_score = risk_map.get(int(prediction), ("Unknown", 0))

    print(f"INPUT: HR={hr} BP={sys_bp}/{dia} SpO2={spo2} Stress={stress}  →  {risk_text}")

    data["risk"]       = risk_text
    data["risk_score"] = risk_score

    if risk_text == "Emergency" and latest_data.get("risk") != "Emergency":
        pending_sms = True
        # ── FALLBACK SMS (no GPS yet) ───────────────────────────────
        # Sent immediately so the guardian is notified even if the
        # browser never calls /send-emergency-location (e.g. tab closed).
        # The browser will also call that endpoint within ~1 s with GPS.
        fallback_msg = (
            f"🚨 EMERGENCY ALERT!\n"
            f"She is in danger — please help immediately ⚠️\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💓 Heart Rate : {hr} bpm\n"
            f"🩸 BP         : {sys_bp}/{dia} mmHg\n"
            f"🫁 SpO2       : {spo2}%\n"
            f"🧠 Stress     : {stress}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📍 GPS location will follow in a second SMS."
        )
        send_sms(fallback_msg)

    latest_data = data
    return jsonify({"status": "received"})


# ====================================================================
# BROWSER PUSHES GPS WHEN EMERGENCY FIRES  →  second SMS with location
# ====================================================================
@app.route("/send-emergency-location", methods=["POST"])
def send_emergency_location():
    global pending_sms

    if not pending_sms:
        # Duplicate call — ignore (popup dismissed and re-opened etc.)
        return jsonify({"status": "skipped"})

    d         = request.json or {}
    location  = d.get("location",  "Unknown")
    maps_link = d.get("maps_link", "")
    hr        = d.get("heart_rate", "--")
    bp        = d.get("bp",         "--/--")
    spo2      = d.get("spo2",       "--")
    stress    = d.get("stress",     "--")
    g_name    = guardian["name"] or "Guardian"

    maps_line = f"\n🗺️ Open Maps: {maps_link}" if maps_link else ""
    msg = (
        f"📍 GPS LOCATION UPDATE\n"
        f"(Following the Emergency Alert just sent)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Location : {location}{maps_line}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💓 HR  : {hr}   🫁 SpO2: {spo2}\n"
        f"🩸 BP  : {bp}   🧠 Stress: {stress}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Please respond immediately, {g_name}!"
    )

    ok = send_sms(msg)
    pending_sms = False
    print(f"GPS SMS {'SENT' if ok else 'FAILED'} → {location}  {maps_link}")
    return jsonify({"status": "sent" if ok else "failed"})


# ====================================================================
# FRONTEND POLL
# ====================================================================
@app.route("/watch-data")
def watch_data():
    return jsonify(latest_data)


# ====================================================================
# RESEND SOS  (popup button)
# ====================================================================
@app.route("/resend-sos", methods=["POST"])
def resend_sos():
    d         = request.json or {}
    location  = d.get("location",  "Unknown location")
    maps_link = d.get("maps_link", "")
    hr        = d.get("heart_rate", "--")
    bp        = d.get("bp",         "--/--")
    spo2      = d.get("spo2",       "--")
    stress    = d.get("stress",     "--")
    g_name    = guardian["name"] or "Guardian"

    maps_line = f"\n🗺️ Open Maps: {maps_link}" if maps_link else ""
    msg = (
        f"🆘 SOS RESENT — STILL IN DANGER!\n"
        f"{g_name}, she still needs help ⚠️\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📍 Location : {location}{maps_line}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💓 HR  : {hr}   🫁 SpO2: {spo2}\n"
        f"🩸 BP  : {bp}   🧠 Stress: {stress}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"Please respond immediately!"
    )

    ok = send_sms(msg)
    print(f"RESEND SOS {'SENT' if ok else 'FAILED'} → {location}")
    return jsonify({"status": "sent" if ok else "failed"})


if __name__ == "__main__":
    app.run(debug=True)

"""
Myanmar Astrology Chatbot — Flask Backend

Provides a ChatGPT-style conversational interface for Mahabote astrology readings.
All responses are in Myanmar language.
"""

import os
import re
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session

from mahabote_engine import MahaboteEngine, MahaboteReading
from pdf_generator import generate_pdf
from sheets_sync import sync_new_booking, sync_status_update

app = Flask(__name__)
app.secret_key = os.urandom(24)

engine = MahaboteEngine()

# In-memory session store (for simplicity)
sessions = {}

# Bookings storage (JSON file)
# Use Modal persistent Volum if /data exists, otherwise use local dir
if os.path.exists("/data"):
    BOOKINGS_FILE = "/data/bookings.json"
else:
    BOOKINGS_FILE = os.path.join(os.path.dirname(__file__), "bookings.json")


import fcntl
import tempfile

def load_bookings():
    """Load bookings from JSON file with file locking."""
    if not os.path.exists(BOOKINGS_FILE):
        return []
    try:
        with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = f.read()
                if not data.strip():
                    return []
                return json.loads(data)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception as e:
        print(f"Error reading bookings.json: {e}")
        return []

def save_bookings(bookings):
    """Save bookings to JSON file atomically."""
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(BOOKINGS_FILE)), text=True)
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            json.dump(bookings, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, BOOKINGS_FILE)
    except Exception as e:
        print(f"Error saving bookings.json: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)


import threading

db_lock = threading.Lock()

def _update_bookings(modifier_func):
    """
    Safely update bookings using an exclusive thread lock.
    The modifier_func should take the bookings list and return (new_bookings_list, return_value).
    If new_bookings_list is None, nothing gets saved.
    """
    with db_lock:
        bookings = load_bookings()
        updated_bookings, ret_val = modifier_func(bookings)
        if updated_bookings is not None:
            save_bookings(updated_bookings)
        return ret_val


def get_session_data():
    """Get or create session data."""
    sid = session.get("sid")
    if not sid or sid not in sessions:
        sid = str(uuid.uuid4())
        session["sid"] = sid
        sessions[sid] = {
            "state": "greeting",
            "name": None,
            "dob": None,
            "is_wednesday_pm": False,
            "reading": None,
            "history": [],
        }
    return sessions[sid]


@app.route("/")
def index():
    """Serve the chatbot frontend."""
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """Process a chat message and return the bot response."""
    data = request.get_json()
    user_msg = data.get("message", "").strip()

    sess = get_session_data()
    sess["history"].append({"role": "user", "content": user_msg})

    response = process_message(sess, user_msg)

    sess["history"].append({"role": "bot", "content": response})

    return jsonify({
        "response": response,
        "state": sess["state"],
        "has_reading": sess["reading"] is not None,
    })


@app.route("/api/init", methods=["GET"])
def init_chat():
    """Initialize a new chat session and return the greeting."""
    sess = get_session_data()
    greeting = engine.get_greeting_message()
    sess["history"].append({"role": "bot", "content": greeting})
    return jsonify({
        "response": greeting,
        "state": "greeting",
    })




# ── Booking Routes ───────────────────────────────────────────

@app.route("/booking")
def booking_page():
    """Serve the appointment booking page."""
    return render_template("booking.html")


@app.route("/admin")
def admin_page():
    """Serve the admin dashboard."""
    return render_template("admin.html")


@app.route("/api/bookings/status", methods=["POST"])
def update_booking_status():
    """Update a booking's status (confirm/reject) and sync to Sheets."""
    data = request.get_json()
    booking_id = data.get("booking_id")
    new_status = data.get("status")

    if not booking_id or new_status not in ("confirmed", "rejected", "pending"):
        return jsonify({"error": "Invalid booking_id or status"}), 400

    def modify_status(bookings_list):
        for b in bookings_list:
            if b["booking_id"] == booking_id:
                b["status"] = new_status
                return bookings_list, b
        return None, None

    updated_booking = _update_bookings(modify_status)

    if not updated_booking:
        return jsonify({"error": "Booking not found"}), 404

    # Send status update to n8n → SMS + Sheets
    try:
        sync_status_update(updated_booking, new_status)
    except Exception as e:
        print(f"⚠️ n8n sync failed: {e}")

    return jsonify({"message": f"Booking {booking_id} → {new_status}"})

@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    """Return all bookings."""
    bookings = load_bookings()
    return jsonify({"bookings": bookings})


@app.route("/api/bookings/<booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    """Delete a booking."""
    def remove_booking(bookings_list):
        initial_len = len(bookings_list)
        bookings_list = [b for b in bookings_list if b["booking_id"] != booking_id]
        if len(bookings_list) == initial_len:
            return None, False
        return bookings_list, True

    deleted = _update_bookings(remove_booking)

    if not deleted:
        return jsonify({"error": "Booking not found"}), 404

    return jsonify({"message": f"Booking {booking_id} deleted"}), 200


@app.route("/api/bookings", methods=["POST"])
def create_booking():
    """Create a new appointment booking."""
    data = request.get_json()

    # Validate required fields
    required = ["name", "phone", "date", "time"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    # Create booking
    booking_id = "BK-" + datetime.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4())[:6].upper()
    booking = {
        "booking_id": booking_id,
        "name": data["name"],
        "phone": data["phone"],
        "date": data["date"],
        "time": data["time"],
        "topic": data.get("topic", "general"),
        "note": data.get("note", ""),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }

    def add_booking(bookings_list):
        bookings_list.insert(0, booking)  # newest first
        return bookings_list, True

    _update_bookings(add_booking)

    # Send to n8n → Google Sheets
    try:
        sync_new_booking(booking)
    except Exception as e:
        print(f"⚠️ n8n sync failed: {e}")

    return jsonify({"booking_id": booking_id, "message": "Booking created successfully"}), 201




# ── Tarot vs Mahabote Promotion (40,000 MMK) ─────────────────
PROMO_MSG = (
    "\n═══════════════════════════════════\n"
    "🔮 **Tarot vs မဟာဘုတ် — ဘာကွာလဲ?**\n"
    "═══════════════════════════════════\n\n"
    "📖 **မဟာဘုတ် ဗေဒင်** (အခမဲ့ — ယခု ရရှိပြီး)\n"
    "• မွေးနေ့ အခြေပြု ယေဘူယျ ဟောကိန်းများ\n"
    "• ၆ လ ခန့်မှန်းခြင်း (အထွေထွေ)\n"
    "• ကံကြမ္မာ လမ်းကြောင်း အကြမ်းဖျင်း\n\n"
    "🃏 **Tarot ကတ် ဖတ်ခြင်း** (40,000 ကျပ်)\n"
    "• သင့်ဘဝ အခြေအနေ တိတိပပ ဖတ်ခြင်း\n"
    "• အချစ်ရေး၊ အလုပ်၊ ငွေကြေး → တိကျသော အဖြေများ\n"
    "• ရှောင်ရန်/လုပ်ရန် အသေးစိတ် လမ်းညွှန်ချက်\n"
    "• Su Mon Myint Oo နှင့် တိုက်ရိုက် ဆွေးနွေး\n\n"
    "💰 **အထူးစျေးနှုန်း: ၄၀,၀၀၀ ကျပ် (KPay ဖြင့် ပေးချေနိုင်ပါသည်)** 💰\n\n"
    "🎯 မဟာဘုတ်က ကံကြမ္မာ လမ်းကြောင်းကို ပြပါတယ်...\n"
    "🃏 Tarot က **ဘယ်လို ရွေးချယ်ရမလဲ** ကို ပြပါတယ်!\n\n"
    "📅 ရက်ချိန်း ယူရန် → `ရက်ချိန်း` ဟု ရိုက်ထည့်ပါ\n"
    "👉 သို့ [ရက်ချိန်း ယူရန်](/booking)"
)


def process_message(sess: dict, user_msg: str) -> str:
    """State machine for processing chat messages."""
    state = sess["state"]

    if state == "greeting":
        # User should provide their name
        if len(user_msg) < 1:
            return "ကျေးဇူးပြု၍ သင့်ရဲ့ အမည်ကို ရိုက်ထည့်ပေးပါ။ 🙏"

        sess["name"] = user_msg
        sess["state"] = "ask_dob"
        return engine.get_dob_prompt(user_msg)

    elif state == "ask_dob":
        # Parse date of birth
        dob = parse_date(user_msg)
        if not dob:
            return (
                "❌ ရက်စွဲ ပုံစံ မမှန်ပါ။\n\n"
                "ကျေးဇူးပြု၍ `YYYY-MM-DD` ပုံစံဖြင့် ထပ်မံ ရိုက်ထည့်ပေးပါ။\n"
                "ဥပမာ: `1990-05-15` 📅"
            )

        sess["dob"] = dob

        # Check if it's a Wednesday
        from myanmar_calendar import get_weekday_index, w2j
        jdn = w2j(dob.year, dob.month, dob.day, ct=1)
        wd = (jdn + 2) % 7  # 0=Sat, 4=Wed
        if wd == 4:
            sess["state"] = "ask_wednesday"
            return engine.get_wednesday_prompt()
        else:
            return compute_reading(sess)

    elif state == "ask_wednesday":
        # Parse Wednesday morning/afternoon
        msg_lower = user_msg.lower()
        if "ညနေ" in user_msg or "afternoon" in msg_lower or "pm" in msg_lower or "ညနေ" in user_msg:
            sess["is_wednesday_pm"] = True
        elif "နံနက်" in user_msg or "morning" in msg_lower or "am" in msg_lower:
            sess["is_wednesday_pm"] = False
        else:
            return (
                "ကျေးဇူးပြု၍ `နံနက်` (morning) သို့မဟုတ် `ညနေ` (afternoon) "
                "ဟု ရိုက်ထည့်ပေးပါ။ ⏰"
            )

        return compute_reading(sess)

    elif state == "reading_shown":
        # Any subsequent message can just reiterate the promo or answer general questions
        msg_lower = user_msg.lower()
        if any(kw in user_msg for kw in ["ကျေးဇူး", "thank", "ကောင်း"]):
            return (
                "ရပါတယ်ရှင်၊ အချိန်မရွေး ထပ်မံ မေးမြန်းနိုင်ပါတယ်။\n\n"
                "Tarot ရက်ချိန်း ယူလိုပါက `ရက်ချိန်း` ဟု ရိုက်ထည့်ပါ။ 🙏"
            )
        else:
            return (
                "Tarot ရက်ချိန်း ယူလိုပါက `ရက်ချိန်း` ဟု ရိုက်ထည့်ပါ။\n\n"
                "အခြား မေးခွန်း ရှိပါက မေးမြန်းနိုင်ပါတယ်။ 🙏"
            )

    # Handle booking keyword in any state
    if any(kw in user_msg for kw in ["ရက်ချိန်း", "appointment", "book"]):
        return (
            "📅 **Tarot ရက်ချိန်း** ယူရန် အောက်ပါ link ကို နှိပ်ပါ:\n\n"
            "👉 [ရက်ချိန်း ယူရန်](/booking)\n\n"
            "Su Mon Myint Oo နှင့် ဗေဒင် တိုက်ရိုက် ဆွေးနွေးနိုင်ပါမည်။ 🔮"
        )

    return "🙏 ကျေးဇူးပြု၍ ထပ်မံ စတင်ရန် စာမျက်နှာကို refresh လုပ်ပါ။"


def compute_reading(sess: dict) -> str:
    """Compute the Mahabote reading and format the response."""
    dob = sess["dob"]
    try:
        reading = engine.calculate(
            name=sess["name"],
            birth_year=dob.year,
            birth_month=dob.month,
            birth_day=dob.day,
            is_wednesday_pm=sess["is_wednesday_pm"],
        )
        sess["reading"] = reading
        sess["state"] = "reading_shown"
        return engine.format_reading(reading) + PROMO_MSG
    except Exception as e:
        return f"❌ တွက်ချက်ရာတွင် အမှားရှိပါသည်: {str(e)}\nကျေးဇူးပြု၍ ထပ်မံ ကြိုးစားပါ။"


def parse_date(text: str) -> datetime:
    """Parse a date from user text input."""
    text = text.strip()

    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y.%m.%d",
        "%m-%d-%Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(text, fmt)
            # Sanity check: reasonable birth year
            if 1900 <= dt.year <= datetime.now().year:
                return dt
        except ValueError:
            continue

    # Try to extract date from free text
    match = re.search(r'(\d{4})\s*[-/.]?\s*(\d{1,2})\s*[-/.]?\s*(\d{1,2})', text)
    if match:
        try:
            y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            dt = datetime(y, m, d)
            if 1900 <= dt.year <= datetime.now().year:
                return dt
        except (ValueError, OverflowError):
            pass

    return None


if __name__ == "__main__":
    os.makedirs("static/reports", exist_ok=True)
    os.makedirs("fonts", exist_ok=True)
    print("🔮 Myanmar Astrology Chatbot starting...")
    print("   Open http://localhost:5050 in your browser")
    app.run(debug=True, host="0.0.0.0", port=5050)

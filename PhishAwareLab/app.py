import os
import re
import ssl
import json
import time
import random
import smtplib
import threading
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')
file_lock = threading.RLock()
simulation_thread = None
simulation_running = False

# In-memory recent event cache for duplicate detection (fingerprint -> timestamp)
_recent_event_cache = {}

DEFAULT_DATA = {
    "stats": {
        "sent": 30,
        "opened": 22,
        "clicked": 14,
        "submitted": 8,
        "open_rate": 73.3,
        "click_rate": 46.7,
        "submit_rate": 26.7
    },
    "status": "Simulation Active",
    "is_running": False,
    "recent_activity": [
        {
            "id": 1,
            "user": "User 05",
            "action": "Simulated submission recorded",
            "type": "submitted",
            "details": "Mock credential submission intercepted on sandbox training page",
            "timestamp": "09:23:45"
        },
        {
            "id": 2,
            "user": "User 14",
            "action": "Training link interaction simulated",
            "type": "clicked",
            "details": "Interaction detected with simulated awareness link",
            "timestamp": "09:22:10"
        },
        {
            "id": 3,
            "user": "User 22",
            "action": "Test email opened",
            "type": "opened",
            "details": "Simulated security advisory notification viewed",
            "timestamp": "09:20:30"
        },
        {
            "id": 4,
            "user": "User 08",
            "action": "Awareness test completed",
            "type": "completed",
            "details": "Completed instant feedback learning module on phishing indicators",
            "timestamp": "09:18:15"
        },
        {
            "id": 5,
            "user": "System",
            "action": "Simulation started",
            "type": "system",
            "details": "Ethical hacking training simulation scenario initialized",
            "timestamp": "09:15:00"
        }
    ]
}

def normalize_event_type(raw_type):
    """
    Normalizes any common variant of event type into canonical form:
    'sent', 'opened', 'clicked', 'submitted'.
    Returns None if the type is invalid or unrecognized.
    Note: General web page visits are NOT mapped to 'opened' to adhere to ethical
    telemetry standards (email open measurements are distinct from page loads).
    """
    if not raw_type:
        return None
    val = str(raw_type).strip().lower()
    if val in {'sent', 'send', 'dispatch', 'dispatched'}:
        return 'sent'
    if val in {'opened', 'open', 'email_opened', 'demo_open', 'manual_open'}:
        return 'opened'
    if val in {'clicked', 'click', 'link_clicked', 'interaction', 'interacted'}:
        return 'clicked'
    if val in {'completed', 'complete', 'submitted', 'submit', 'submission'}:
        return 'submitted'
    return None

def is_duplicate_event(user_or_volunteer, norm_type, window_seconds=15.0):
    """
    Checks if an identical event was submitted within the given time window.
    Prevents unintended duplicate counts from rapid re-submissions or page refreshes.
    """
    global _recent_event_cache
    now = time.time()
    # Prune entries older than 60 seconds
    _recent_event_cache = {k: t for k, t in _recent_event_cache.items() if (now - t) < 60.0}

    key = f"{str(user_or_volunteer).strip().lower()}:{norm_type}"
    last_time = _recent_event_cache.get(key)
    if last_time and (now - last_time) < window_seconds:
        return True

    _recent_event_cache[key] = now
    return False

def load_data():
    """Safely loads simulation statistics and activity from data.json."""
    with file_lock:
        if not os.path.exists(DATA_FILE):
            save_data_internal(DEFAULT_DATA)
            return json.loads(json.dumps(DEFAULT_DATA))
        for _ in range(5):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, PermissionError, OSError):
                time.sleep(0.02)
        return json.loads(json.dumps(DEFAULT_DATA))

def save_data_internal(data):
    """Internal helper to write data to data.json atomically and safely."""
    temp_file = f"{DATA_FILE}.tmp.{os.getpid()}.{threading.get_ident()}"
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        for _ in range(5):
            try:
                os.replace(temp_file, DATA_FILE)
                return
            except (PermissionError, OSError):
                time.sleep(0.02)
        # Fallback direct write if os.replace fails
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

def save_data(data):
    """Safely saves simulation statistics and activity to data.json."""
    with file_lock:
        save_data_internal(data)

def run_synthetic_simulation():
    """
    Background worker simulating ethical phishing awareness events.
    All events use fictional IDs (e.g., User 01 - User 30) and local test telemetry.
    No actual emails or real credential collection occurs.
    """
    global simulation_running
    steps = [
        ("sent", "Test email dispatched", "Simulated IT security upgrade prompt delivered", "sent"),
        ("opened", "Test email opened", "Simulated awareness scenario email previewed", "opened"),
        ("clicked", "Training link interaction simulated", "Interaction with safe educational link recorded", "clicked"),
        ("completed", "Awareness test completed", "Participant correctly flagged suspicious link indicators", "completed"),
        ("submitted", "Simulated submission recorded", "Test submission captured on safe demonstration form", "submitted"),
        ("opened", "Test email opened", "Follow-up training advisory email opened", "opened"),
        ("clicked", "Training link interaction simulated", "Simulated awareness portal link clicked", "clicked"),
        ("completed", "Awareness test completed", "Interactive phishing recognition tutorial finished", "completed")
    ]

    for step_type, action_name, details, category in steps:
        if not simulation_running:
            break

        time.sleep(2.0)  # Interval between synthetic events
        if not simulation_running:
            break

        with file_lock:
            try:
                current_data = load_data()
            except Exception:
                current_data = json.loads(json.dumps(DEFAULT_DATA))

            # Increment relevant metric independently (no artificial progression)
            norm_key = normalize_event_type(step_type) or "submitted"
            stats = current_data.setdefault("stats", {"sent": 30, "opened": 22, "clicked": 14, "submitted": 8})
            stats[norm_key] = stats.get(norm_key, 0) + 1

            # Generate fictional participant label (User 01 - User 30)
            user_num = random.randint(1, 30)
            user_label = f"User {user_num:02d}"

            now_str = datetime.now().strftime("%H:%M:%S")

            new_activity = {
                "id": int(time.time() * 1000),
                "user": user_label,
                "action": action_name,
                "type": category,
                "details": details,
                "timestamp": now_str
            }

            # Prepend new activity and keep top 25
            current_data.setdefault("recent_activity", []).insert(0, new_activity)
            current_data["recent_activity"] = current_data["recent_activity"][:25]
            current_data["status"] = "Simulation Active"
            current_data["is_running"] = True

            sent_val = stats.get("sent", 0)
            stats["open_rate"] = round((stats.get("opened", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["click_rate"] = round((stats.get("clicked", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["submit_rate"] = round((stats.get("submitted", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["completed"] = stats.get("submitted", 0)

            save_data_internal(current_data)

    # When all simulation steps finish
    with file_lock:
        try:
            current_data = load_data()
            current_data["is_running"] = False
            save_data_internal(current_data)
        except Exception:
            pass

    simulation_running = False

@app.route('/')
def index():
    """Renders the main PhishAwareLab cybersecurity dashboard."""
    return render_template('dashboard.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Returns current dashboard statistics, rates, and recent activity as JSON.
    Polled every 2 seconds by the frontend.
    """
    data = load_data()
    stats = data.get("stats", {})
    sent = stats.get("sent", 0)
    opened = stats.get("opened", 0)
    clicked = stats.get("clicked", 0)
    submitted = stats.get("submitted", 0)

    # Compute percentages safely
    open_rate = round((opened / sent * 100), 1) if sent > 0 else 0.0
    click_rate = round((clicked / sent * 100), 1) if sent > 0 else 0.0
    submit_rate = round((submitted / sent * 100), 1) if sent > 0 else 0.0

    return jsonify({
        "status": data.get("status", "Simulation Active"),
        "is_running": simulation_running,
        "stats": {
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "submitted": submitted,
            "completed": submitted,
            "open_rate": open_rate,
            "click_rate": click_rate,
            "submit_rate": submit_rate
        },
        "recent_activity": data.get("recent_activity", []),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/api/start-demo', methods=['POST'])
def start_demo():
    """
    Starts a local synthetic demonstration with simulated participant events.
    Uses only safe synthetic telemetry.
    """
    global simulation_thread, simulation_running

    if simulation_running:
        return jsonify({
            "success": True,
            "message": "Demo simulation is already running.",
            "is_running": True
        })

    simulation_running = True
    simulation_thread = threading.Thread(target=run_synthetic_simulation, daemon=True)
    simulation_thread.start()

    return jsonify({
        "success": True,
        "message": "Synthetic demo started! Events will stream in live.",
        "is_running": True
    })

@app.route('/api/reset-demo', methods=['POST'])
def reset_demo():
    """
    Resets the demo statistics and activity back to the baseline sample values:
    Sent: 30, Opened: 22, Clicked: 14, Submitted: 8.
    """
    global simulation_running, _recent_event_cache
    simulation_running = False
    _recent_event_cache.clear()

    # Reset data file to default sample values
    reset_data = {
        "stats": {
            "sent": 30,
            "opened": 22,
            "clicked": 14,
            "submitted": 8,
            "open_rate": 73.3,
            "click_rate": 46.7,
            "submit_rate": 26.7
        },
        "status": "Simulation Active",
        "is_running": False,
        "recent_activity": [
            {
                "id": 1,
                "user": "User 05",
                "action": "Simulated submission recorded",
                "type": "submitted",
                "details": "Mock credential submission intercepted on sandbox training page",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            },
            {
                "id": 2,
                "user": "User 14",
                "action": "Training link interaction simulated",
                "type": "clicked",
                "details": "Interaction detected with simulated awareness link",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            },
            {
                "id": 3,
                "user": "User 22",
                "action": "Test email opened",
                "type": "opened",
                "details": "Simulated security advisory notification viewed",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            },
            {
                "id": 4,
                "user": "User 08",
                "action": "Awareness test completed",
                "type": "completed",
                "details": "Completed instant feedback learning module on phishing indicators",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            },
            {
                "id": 5,
                "user": "System",
                "action": "Simulation started",
                "type": "system",
                "details": "Ethical hacking training simulation baseline reset",
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        ]
    }
    save_data(reset_data)

    return jsonify({
        "success": True,
        "message": "Demo statistics and activity have been reset to baseline sample values (30 Invitations Sent, 22 Opens, 14 Link Clicks, 8 Completed).",
        "is_running": False,
        "stats": reset_data["stats"]
    })

@app.route('/api/event/<event_type>', methods=['POST'])
@app.route('/api/event', methods=['POST'])
def trigger_synthetic_event(event_type=None):
    """
    Controlled Event Testing endpoint.
    Generates a single synthetic local event with server-side validation.
    Each event updates ONLY its own counter (no artificial progression):
    - Sent: increments sent count only.
    - Opened: increments opened count only (disclosed manual/demo open).
    - Clicked: increments clicked count only.
    - Completed / Submitted: increments submitted count only.
    Uses fictional participant labels (e.g. Test User 01, Test User 02).
    """
    if event_type is None:
        data_body = request.get_json(silent=True) or {}
        event_type = data_body.get('type') or data_body.get('event_type')

    if not event_type:
        return jsonify({
            "success": False,
            "message": "Missing event type in request."
        }), 400

    norm_type = normalize_event_type(event_type)
    if not norm_type:
        return jsonify({
            "success": False,
            "message": f"Invalid event type '{event_type}'. Permitted types: sent, opened, clicked, completed."
        }), 400

    user_num = random.randint(1, 30)
    user_label = f"Test User {user_num:02d}"
    now_str = datetime.now().strftime("%H:%M:%S")

    if norm_type == 'sent':
        action_name = "Controlled test invitation sent"
        action_type = "sent"
        details = f"Synthetic phishing scenario dispatched to {user_label} (Simulated)"
    elif norm_type == 'opened':
        action_name = "Email open interaction (Demo/Manual)"
        action_type = "opened"
        details = f"Disclosed manual/demo email open recorded for {user_label}"
    elif norm_type == 'clicked':
        action_name = "Disclosed training link activated"
        action_type = "clicked"
        details = f"Participant {user_label} activated disclosed training portal link"
    else:  # submitted
        action_name = "Awareness training completed"
        action_type = "completed"
        details = f"Simulated awareness training & submission logged for {user_label}"

    with file_lock:
        data = load_data()
        stats = data.setdefault("stats", {"sent": 30, "opened": 22, "clicked": 14, "submitted": 8})

        # Increment ONLY its corresponding statistic (NO artificial progression)
        stats[norm_type] = stats.get(norm_type, 0) + 1

        sent_val = stats.get("sent", 0)
        open_rate = round((stats.get("opened", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
        click_rate = round((stats.get("clicked", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
        submit_rate = round((stats.get("submitted", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
        stats["open_rate"] = open_rate
        stats["click_rate"] = click_rate
        stats["submit_rate"] = submit_rate
        stats["completed"] = stats.get("submitted", 0)

        new_activity = {
            "id": int(time.time() * 1000),
            "user": user_label,
            "action": action_name,
            "type": action_type,
            "details": details,
            "timestamp": now_str
        }

        activities = data.setdefault("recent_activity", [])
        activities.insert(0, new_activity)
        data["recent_activity"] = activities[:25]
        data["status"] = "Simulation Active"

        save_data_internal(data)

        return jsonify({
            "success": True,
            "message": f"Recorded synthetic {norm_type.capitalize()} event for {user_label}.",
            "event": new_activity,
            "stats": stats
        })

@app.route('/training')
def training_page():
    """Renders the transparent, consent-based volunteer cybersecurity awareness training page."""
    return render_template('training.html')

@app.route('/api/training/event', methods=['POST'])
@app.route('/api/training/visit', methods=['POST'])
@app.route('/api/training/click', methods=['POST'])
@app.route('/api/training/complete', methods=['POST'])
def record_training_event():
    """
    Records transparent, consent-based volunteer training activity.
    Permits event types:
      - 'clicked': records when volunteer activates disclosed training portal link.
      - 'complete' / 'submitted': records voluntary completion of the red flag identification activity.
      - 'visit': records informational portal arrival without fabricating email open events.
    Does NOT collect passwords, personal information, or credentials.
    Uses generic participant IDs (e.g., Volunteer 04).
    Thread-safe and protected from invalid requests and duplicate submissions.
    """
    body = request.get_json(silent=True) or {}
    
    # Determine event type based on URL path or request payload
    path = request.path.lower()
    if path.endswith('/click'):
        raw_type = 'clicked'
    elif path.endswith('/complete'):
        raw_type = 'complete'
    elif path.endswith('/visit'):
        raw_type = 'visit'
    else:
        raw_type = body.get('type') or body.get('event_type') or 'clicked'

    # Sanitize and assign generic volunteer label (no personal info allowed)
    volunteer_id = body.get('volunteer_id') or body.get('user')
    if not volunteer_id or not isinstance(volunteer_id, str) or not volunteer_id.strip():
        user_num = random.randint(1, 30)
        volunteer_label = f"Volunteer {user_num:02d}"
    else:
        cleaned = volunteer_id.strip()[:20]
        if cleaned.lower().startswith('volunteer'):
            volunteer_label = cleaned
        else:
            volunteer_label = f"Volunteer {cleaned}"

    now_str = datetime.now().strftime("%H:%M:%S")

    # Handle informational portal visit without changing email open counter
    if raw_type == 'visit':
        with file_lock:
            data = load_data()
            stats = data.setdefault("stats", {"sent": 30, "opened": 22, "clicked": 14, "submitted": 8})
        return jsonify({
            "success": True,
            "event_type": "visit",
            "volunteer_id": volunteer_label,
            "message": f"Training page visit recorded for {volunteer_label} (no email open counter altered).",
            "duplicate": False,
            "stats": stats
        })

    norm_type = normalize_event_type(raw_type)
    if not norm_type:
        return jsonify({
            "success": False,
            "message": f"Invalid training event type '{raw_type}'. Permitted types: clicked, complete, opened."
        }), 400

    with file_lock:
        data = load_data()
        stats = data.setdefault("stats", {"sent": 30, "opened": 22, "clicked": 14, "submitted": 8})

        # Deduplication Guard: prevent duplicate visit or completion logs for the same volunteer
        if is_duplicate_event(volunteer_label, norm_type, window_seconds=15.0):
            return jsonify({
                "success": True,
                "event_type": norm_type,
                "volunteer_id": volunteer_label,
                "message": f"Duplicate {norm_type} event ignored for {volunteer_label}.",
                "duplicate": True,
                "stats": stats
            })

        # Assign action name & details based on normalized type
        if norm_type == 'clicked':
            action_name = "Disclosed training link activated"
            action_type = "clicked"
            details = f"Participant {volunteer_label} activated disclosed training portal link"
        elif norm_type == 'submitted':
            action_name = "Awareness training completed"
            action_type = "completed"
            details = f"Volunteer {volunteer_label} completed suspicious email red flag analysis activity"
        elif norm_type == 'opened':
            action_name = "Email open interaction (Demo/Manual)"
            action_type = "opened"
            details = f"Disclosed manual/demo email open recorded for {volunteer_label}"
        else:
            action_name = "Controlled test invitation sent"
            action_type = "sent"
            details = f"Awareness invitation dispatched to {volunteer_label}"

        # Increment ONLY its corresponding statistic (NO artificial progression)
        stats[norm_type] = stats.get(norm_type, 0) + 1

        sent_val = stats.get("sent", 0)
        stats["open_rate"] = round((stats.get("opened", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
        stats["click_rate"] = round((stats.get("clicked", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
        stats["submit_rate"] = round((stats.get("submitted", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
        stats["completed"] = stats.get("submitted", 0)

        new_activity = {
            "id": int(time.time() * 1000),
            "user": volunteer_label,
            "action": action_name,
            "type": action_type,
            "details": details,
            "timestamp": now_str
        }

        activities = data.setdefault("recent_activity", [])
        activities.insert(0, new_activity)
        data["recent_activity"] = activities[:25]
        data["status"] = "Simulation Active"

        save_data_internal(data)

    return jsonify({
        "success": True,
        "event_type": norm_type,
        "volunteer_id": volunteer_label,
        "message": f"Successfully logged {action_name.lower()} for {volunteer_label}.",
        "duplicate": False,
        "event": new_activity,
        "stats": stats
    })

# =========================================================================
# Email Invitation Module (Gmail SMTP & Safe Preview)
# =========================================================================

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def get_smtp_config():
    """Retrieves Gmail SMTP credentials from environment variables."""
    sender_email = (
        os.environ.get('GMAIL_USER') or
        os.environ.get('SMTP_EMAIL') or
        os.environ.get('GMAIL_SENDER') or
        ''
    ).strip()
    app_password = (
        os.environ.get('GMAIL_APP_PASSWORD') or
        os.environ.get('SMTP_APP_PASSWORD') or
        ''
    ).strip().replace(' ', '')
    return sender_email, app_password

def mask_email(email_str):
    """Safely masks an email address for display (e.g. u***@gmail.com)."""
    if not email_str or '@' not in email_str:
        return None
    user_part, domain = email_str.split('@', 1)
    if len(user_part) <= 2:
        masked_user = user_part[0] + '***'
    else:
        masked_user = user_part[0] + '***' + user_part[-1]
    return f"{masked_user}@{domain}"

def build_invitation_content(recipient_email, custom_note=None, training_url="http://127.0.0.1:5000/training"):
    """
    Builds the transparent, consent-based cybersecurity awareness training invitation email.
    Explicitly identifies PhishAwareLab, explains the purpose, contains no stealth tracking,
    and states that no credentials or personal data are ever requested.
    """
    subject = "[PhishAwareLab] Invitation to Volunteer Cybersecurity Awareness Training"

    note_section_text = f"\nNote from Sender:\n{custom_note}\n" if custom_note else ""
    note_section_html = (
        f'<div style="background-color: #f1f5f9; border-left: 4px solid #3b82f6; padding: 12px 16px; margin: 16px 0; border-radius: 4px; color: #1e293b;">'
        f'<strong>Note from Sender:</strong><br>{custom_note}'
        f'</div>'
    ) if custom_note else ""

    text_body = f"""Hello,

You are invited to participate in a transparent, voluntary cybersecurity awareness training exercise hosted by PhishAwareLab (an academic ethical hacking mini-project).
{note_section_text}
Purpose of this Activity:
- Learn how to recognize common social engineering and email phishing indicators (lookalike domains, urgency tactics, deceptive hyperlinks).
- Review a safe, interactive demonstration scenario.
- Estimated completion time: 2 to 3 minutes.

Access the Volunteer Training Module:
{training_url}

Privacy & Ethics Commitment:
- PhishAwareLab NEVER requests passwords, login credentials, or sensitive personal data.
- This email contains ZERO covert open-tracking pixels or deceptive click-redirects.
- Participation is 100% voluntary and anonymous.

Thank you for helping promote cybersecurity awareness!

Sincerely,
PhishAwareLab Project Team
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }}
  .header {{ background: #0f172a; color: #ffffff; padding: 24px; text-align: center; }}
  .header h1 {{ margin: 0; font-size: 20px; color: #38bdf8; }}
  .header p {{ margin: 6px 0 0; font-size: 13px; color: #94a3b8; }}
  .content {{ padding: 24px; }}
  .btn {{ display: inline-block; background: #2563eb; color: #ffffff !important; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: 600; margin: 16px 0; }}
  .notice {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 6px; padding: 14px; font-size: 13px; color: #065f46; margin-top: 20px; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px; font-size: 12px; color: #64748b; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>PhishAwareLab</h1>
    <p>Volunteer Cybersecurity Awareness Training Invitation</p>
  </div>
  <div class="content">
    <p>Hello,</p>
    <p>You have been invited to participate in a <strong>transparent, voluntary cybersecurity awareness training exercise</strong> hosted by the PhishAwareLab academic mini-project.</p>
    
    {note_section_html}

    <h3 style="color: #0f172a; font-size: 15px; margin-top: 20px;">What You Will Learn:</h3>
    <ul style="color: #334155; padding-left: 20px;">
      <li>Spotting lookalike and spoofed sender email domains</li>
      <li>Identifying psychological pressure and artificial urgency</li>
      <li>Examining deceptive hyperlink destinations</li>
    </ul>

    <div style="text-align: center;">
      <a href="{training_url}" class="btn">Open Volunteer Training Portal &rarr;</a>
    </div>

    <div class="notice">
      <strong>Transparent & Safe:</strong> PhishAwareLab never collects passwords, login credentials, or personal information. There are no covert tracking pixels or deceptive redirects in this invitation.
    </div>
  </div>
  <div class="footer">
    PhishAwareLab &bull; Academic Ethical Hacking Mini-Project &bull; Educational Demonstration Only
  </div>
</div>
</body>
</html>
"""
    return subject, text_body, html_body

@app.route('/invite')
def invite_page():
    """Renders the Email Invitation module page."""
    sender_email, app_password = get_smtp_config()
    smtp_configured = bool(sender_email and app_password)
    masked_sender = mask_email(sender_email) if sender_email else None
    return render_template(
        'invite.html',
        smtp_configured=smtp_configured,
        masked_sender=masked_sender
    )

@app.route('/api/invite/status', methods=['GET'])
def get_invite_status():
    """Returns the current SMTP setup status (without exposing credentials)."""
    sender_email, app_password = get_smtp_config()
    return jsonify({
        "smtp_configured": bool(sender_email and app_password),
        "sender_email": mask_email(sender_email) if sender_email else None
    })

@app.route('/api/invite/preview', methods=['POST'])
def preview_invitation():
    """Returns the email subject and preview content for the invitation form."""
    body = request.get_json(silent=True) or {}
    recipient_email = (body.get('recipient_email') or '').strip()
    custom_note = (body.get('custom_note') or '').strip()

    if not recipient_email or not EMAIL_REGEX.match(recipient_email):
        recipient_display = "volunteer@example.com"
    else:
        recipient_display = recipient_email

    training_url = request.host_url.rstrip('/') + '/training?source=email'
    subject, text_body, html_body = build_invitation_content(recipient_display, custom_note, training_url)

    return jsonify({
        "success": True,
        "subject": subject,
        "recipient": recipient_display,
        "text_preview": text_body,
        "html_preview": html_body
    })

@app.route('/api/invite/send', methods=['POST'])
def send_invitation():
    """
    Sends an educational invitation via Gmail SMTP, or validates in Safe Test Mode (dry run).
    Credentials are read from GMAIL_USER and GMAIL_APP_PASSWORD.
    Never exposes passwords. Rejects malformed recipient emails.
    """
    body = request.get_json(silent=True) or {}
    recipient_email = (body.get('recipient_email') or '').strip()
    custom_note = (body.get('custom_note') or '').strip()
    dry_run = bool(body.get('dry_run', False))

    # Validate recipient email format
    if not recipient_email:
        return jsonify({
            "success": False,
            "message": "Recipient email address is required."
        }), 400

    if not EMAIL_REGEX.match(recipient_email):
        return jsonify({
            "success": False,
            "message": f"Invalid email format: '{recipient_email}'. Please enter a valid email address (e.g., volunteer@example.com)."
        }), 400

    training_url = request.host_url.rstrip('/') + '/training?source=email'
    subject, text_body, html_body = build_invitation_content(recipient_email, custom_note, training_url)

    # Safe Test Mode (Dry Run) - validates and previews without contacting external servers
    if dry_run:
        now_str = datetime.now().strftime("%H:%M:%S")
        new_activity = {
            "id": int(time.time() * 1000),
            "user": "System",
            "action": "Training invitation simulated (Test Mode)",
            "type": "sent",
            "details": f"Simulated training invitation generated for {recipient_email} (Test Mode - No Real Email Dispatched)",
            "timestamp": now_str
        }

        with file_lock:
            data = load_data()
            stats = data.setdefault("stats", {"sent": 30, "opened": 22, "clicked": 14, "submitted": 8})
            stats["sent"] += 1
            sent_val = stats.get("sent", 0)
            stats["open_rate"] = round((stats.get("opened", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["click_rate"] = round((stats.get("clicked", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["submit_rate"] = round((stats.get("submitted", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["completed"] = stats.get("submitted", 0)
            activities = data.setdefault("recent_activity", [])
            activities.insert(0, new_activity)
            data["recent_activity"] = activities[:25]
            save_data_internal(data)

        return jsonify({
            "success": True,
            "dry_run": True,
            "recipient": recipient_email,
            "message": f"Safe Test Mode: Invitation for {recipient_email} generated (Simulated event - no real email was sent).",
            "event": new_activity,
            "stats": stats
        })

    # Live Gmail SMTP Mode
    sender_email, app_password = get_smtp_config()
    if not sender_email or not app_password:
        return jsonify({
            "success": False,
            "message": "Gmail SMTP credentials not configured. Please set GMAIL_USER and GMAIL_APP_PASSWORD environment variables, or check 'Safe Test Mode' to preview."
        }), 400

    # Compose message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"PhishAwareLab <{sender_email}>"
    msg['To'] = recipient_email
    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    # Send through Gmail SMTP securely
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=12) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        now_str = datetime.now().strftime("%H:%M:%S")
        new_activity = {
            "id": int(time.time() * 1000),
            "user": "System",
            "action": "Training invitation dispatched (Live SMTP)",
            "type": "sent",
            "details": f"Educational awareness invitation sent to {recipient_email} via Gmail SMTP",
            "timestamp": now_str
        }

        with file_lock:
            data = load_data()
            stats = data.setdefault("stats", {"sent": 30, "opened": 22, "clicked": 14, "submitted": 8})
            stats["sent"] += 1
            sent_val = stats.get("sent", 0)
            stats["open_rate"] = round((stats.get("opened", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["click_rate"] = round((stats.get("clicked", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["submit_rate"] = round((stats.get("submitted", 0) / sent_val * 100), 1) if sent_val > 0 else 0.0
            stats["completed"] = stats.get("submitted", 0)
            activities = data.setdefault("recent_activity", [])
            activities.insert(0, new_activity)
            data["recent_activity"] = activities[:25]
            save_data_internal(data)

        return jsonify({
            "success": True,
            "dry_run": False,
            "recipient": recipient_email,
            "message": f"Invitation successfully delivered to {recipient_email} via Gmail SMTP!",
            "event": new_activity,
            "stats": stats
        })

    except smtplib.SMTPAuthenticationError:
        return jsonify({
            "success": False,
            "message": "Gmail SMTP Authentication Failed. Please check GMAIL_USER and ensure GMAIL_APP_PASSWORD is a valid 16-character Google App Password (not your normal Gmail password)."
        }), 401
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError) as e:
        return jsonify({
            "success": False,
            "message": f"SMTP Network Error: Could not connect to smtp.gmail.com:587. Check your network or firewall connection."
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Failed to send email: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Initialize data file on startup if absent
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
    app.run(debug=True, host='127.0.0.1', port=5000)

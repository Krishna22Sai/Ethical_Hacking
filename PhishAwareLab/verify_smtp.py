"""
PhishAwareLab - Gmail SMTP Diagnostic & Verification Tool
Safely verifies Gmail SMTP connection and authentication over TLS.
Does NOT send any emails or expose credentials.
"""

import os
import sys
import ssl
import smtplib

def mask_email(email_str):
    """Safely masks an email address (e.g., u***@gmail.com) for safe logging."""
    if not email_str or '@' not in email_str:
        return "[INVALID FORMAT]"
    user_part, domain = email_str.split('@', 1)
    if len(user_part) <= 2:
        masked_user = user_part[0] + '***'
    else:
        masked_user = user_part[0] + '***' + user_part[-1]
    return f"{masked_user}@{domain}"

def verify_smtp():
    print("=" * 65)
    print(" PhishAwareLab - Gmail SMTP Configuration Verification")
    print("=" * 65)

    # 1. Detect Environment Variables
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
    ).strip().replace(' ', '')  # Strip whitespace from Google App Passwords

    print("\n[Step 1/3] Checking Environment Variables:")
    if sender_email:
        print(f"  ✓ GMAIL_USER: Detected ({mask_email(sender_email)})")
    else:
        print("  ✗ GMAIL_USER: Missing")

    if app_password:
        print(f"  ✓ GMAIL_APP_PASSWORD: Detected ({len(app_password)} characters, password hidden)")
    else:
        print("  ✗ GMAIL_APP_PASSWORD: Missing")

    # If missing, provide helpful setup commands
    if not sender_email or not app_password:
        print("\n" + "-" * 65)
        print("  [ACTION REQUIRED] Environment variables not set.")
        print("-" * 65)
        print("  Before running this test, set them in your terminal:\n")
        print("  In Windows PowerShell:")
        print('    $env:GMAIL_USER = "your-email@gmail.com"')
        print('    $env:GMAIL_APP_PASSWORD = "your-16-char-app-password"')
        print("    python verify_smtp.py\n")
        print("  In Windows Command Prompt (CMD):")
        print('    set GMAIL_USER=your-email@gmail.com')
        print('    set GMAIL_APP_PASSWORD=your-16-char-app-password')
        print("    python verify_smtp.py\n")
        print("  Note: Generate an App Password at: https://myaccount.google.com/apppasswords")
        print("=" * 65)
        return False

    # 2. Test SMTP Connection over TLS
    smtp_host = "smtp.gmail.com"
    smtp_port = 587

    print(f"\n[Step 2/3] Establishing TLS Connection to {smtp_host}:{smtp_port}...")
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=12)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        print("  ✓ TLS handshake successful (Encrypted channel established)")
    except smtplib.SMTPConnectError:
        print(f"  ✗ Connection failed: Unable to connect to {smtp_host}:{smtp_port}")
        return False
    except (TimeoutError, OSError) as e:
        print(f"  ✗ Network error: Could not reach {smtp_host}:{smtp_port} (Timeout or firewall restriction)")
        return False
    except Exception as e:
        print(f"  ✗ TLS negotiation failed: {str(e)}")
        return False

    # 3. Test Authentication (Zero Emails Sent)
    print("\n[Step 3/3] Authenticating with Gmail SMTP...")
    try:
        server.login(sender_email, app_password)
        server.quit()
        print("  ✓ Authentication successful!")
        
        print("\n" + "=" * 65)
        print(" [RESULT] SMTP Connection Verified Successfully!")
        print("=" * 65)
        print(f"  Status       : Authenticated & Ready")
        print(f"  Server       : {smtp_host}:{smtp_port} (STARTTLS)")
        print(f"  Sender       : {mask_email(sender_email)}")
        print(f"  Safety Notice: Zero emails were dispatched during this verification.")
        print("=" * 65 + "\n")
        return True

    except smtplib.SMTPAuthenticationError:
        server.close()
        print("  ✗ Authentication failed (Gmail 535 Error)")
        print("\n" + "-" * 65)
        print("  [TROUBLESHOOTING]:")
        print("  1. Ensure 2-Step Verification is enabled on your Google Account.")
        print("  2. Ensure you are using a 16-character Google App Password, NOT your regular account password.")
        print("  3. App passwords can be generated at: https://myaccount.google.com/apppasswords")
        print("  4. Verify the email address in GMAIL_USER matches the account that generated the App Password.")
        print("-" * 65 + "\n")
        return False

    except Exception as e:
        server.close()
        print(f"  ✗ Unexpected authentication error: {str(e)}")
        return False

if __name__ == '__main__':
    success = verify_smtp()
    sys.exit(0 if success else 1)

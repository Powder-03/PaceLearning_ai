"""
Test script for email sending functionality.
Run this to verify SMTP configuration works.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# SMTP Configuration - Load from environment variables
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # App password from .env file
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "DocLearn")

# Test recipient (send to yourself)
TEST_RECIPIENT = os.getenv("TEST_RECIPIENT", "your-email@example.com")


def test_smtp_connection():
    """Test basic SMTP connection."""
    print(f"\n{'='*50}")
    print("Testing SMTP Connection")
    print(f"{'='*50}")
    print(f"Host: {SMTP_HOST}")
    print(f"Port: {SMTP_PORT}")
    print(f"User: {SMTP_USER}")
    print(f"Password: {'*' * len(SMTP_PASSWORD)}")
    
    try:
        print("\n[1] Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        print("    ✓ Connected!")
        
        print("\n[2] Starting TLS encryption...")
        server.starttls()
        print("    ✓ TLS started!")
        
        print("\n[3] Logging in...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("    ✓ Login successful!")
        
        server.quit()
        print("\n✅ SMTP connection test PASSED!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("\n   Possible causes:")
        print("   1. Wrong password - make sure you're using an App Password")
        print("   2. 2-Step Verification not enabled on your Google account")
        print("   3. App Password expired or revoked")
        print("\n   To fix:")
        print("   1. Go to https://myaccount.google.com/security")
        print("   2. Enable 2-Step Verification")
        print("   3. Go to App passwords and create a new one for 'Mail'")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        return False


def test_send_email():
    """Test sending an actual email."""
    print(f"\n{'='*50}")
    print("Testing Email Send")
    print(f"{'='*50}")
    print(f"To: {TEST_RECIPIENT}")
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🧪 DocLearn Email Test"
        msg["From"] = f"{EMAIL_FROM_NAME} <{SMTP_USER}>"
        msg["To"] = TEST_RECIPIENT
        
        # Email content
        text_content = """
DocLearn Email Test

This is a test email from DocLearn.
If you received this, your email configuration is working correctly!

Cheers,
DocLearn Team
        """
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
                .content { background: #f9f9f9; padding: 20px; border-radius: 0 0 8px 8px; }
                .success { color: #10B981; font-size: 24px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 DocLearn</h1>
                </div>
                <div class="content">
                    <p class="success">✅ Email Test Successful!</p>
                    <p>This is a test email from DocLearn.</p>
                    <p>If you received this, your email configuration is working correctly!</p>
                    <hr>
                    <p><small>This is an automated test email.</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        print("\n[1] Connecting to SMTP server...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            print("    ✓ Connected!")
            
            print("[2] Starting TLS...")
            server.starttls()
            print("    ✓ TLS started!")
            
            print("[3] Logging in...")
            server.login(SMTP_USER, SMTP_PASSWORD)
            print("    ✓ Logged in!")
            
            print("[4] Sending email...")
            server.sendmail(SMTP_USER, TEST_RECIPIENT, msg.as_string())
            print("    ✓ Email sent!")
        
        print(f"\n✅ Email sent successfully to {TEST_RECIPIENT}!")
        print("   Check your inbox (and spam folder) for the test email.")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ Authentication failed: {e}")
        print("   Make sure you're using a Gmail App Password!")
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*50)
    print("   DocLearn Email Configuration Test")
    print("="*50)
    
    # Test 1: SMTP Connection
    connection_ok = test_smtp_connection()
    
    if connection_ok:
        # Test 2: Send actual email
        print("\n")
        send_ok = test_send_email()
        
        if send_ok:
            print("\n" + "="*50)
            print("   🎉 ALL TESTS PASSED!")
            print("="*50)
            print("\nYour email configuration is working correctly.")
            print("Check your inbox for the test email!")
        else:
            print("\n" + "="*50)
            print("   ⚠️ SEND TEST FAILED")
            print("="*50)
    else:
        print("\n" + "="*50)
        print("   ⚠️ CONNECTION TEST FAILED")
        print("="*50)
        print("\nFix the authentication issue before proceeding.")

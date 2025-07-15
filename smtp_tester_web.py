#!/usr/bin/env python3

from flask import Flask, render_template_string, request
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket

app = Flask(__name__)
app.secret_key = 'smtp-secret-key'

# ✅ This is the real HTML that should replace <same as before>
HTML_FORM = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>SMTP Test Tool</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script>
      function toggleAuthFields() {
        var skipAuth = document.getElementById('skipAuthCheck').checked;
        var authFields = document.getElementById('authFields');
        authFields.style.display = skipAuth ? 'none' : 'block';
      }
      window.addEventListener('load', toggleAuthFields);
    </script>
</head>
<body class="bg-light">
<div class="container mt-5">
    <div class="card shadow-sm">
        <div class="card-header bg-primary text-white">
            <h4>SMTP Test Tool</h4>
        </div>
        <div class="card-body">
            <form method="post">
                <div class="mb-3">
                    <label class="form-label">SMTP Server</label>
                    <input type="text" name="server" class="form-control" value="{{ server }}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Port</label>
                    <input type="number" name="port" class="form-control" value="{{ port }}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Encryption</label>
                    <select name="encryption" class="form-select">
                        <option value="none" {% if encryption=='none' %}selected{% endif %}>None</option>
                        <option value="starttls" {% if encryption=='starttls' %}selected{% endif %}>STARTTLS</option>
                        <option value="ssl" {% if encryption=='ssl' %}selected{% endif %}>SSL</option>
                    </select>
                </div>
                <div class="form-check mb-3">
                    <input class="form-check-input" type="checkbox" value="skip" name="skip_auth" id="skipAuthCheck" onclick="toggleAuthFields()" {% if skip_auth %}checked{% endif %}>
                    <label class="form-check-label" for="skipAuthCheck">
                        Skip Authentication
                    </label>
                </div>
                <div id="authFields">
                    <div class="mb-3">
                        <label class="form-label">Username</label>
                        <input type="text" name="username" class="form-control" value="{{ username }}">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Password</label>
                        <input type="password" name="password" class="form-control" value="{{ password }}">
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">From</label>
                    <input type="email" name="from_addr" class="form-control" value="{{ from_addr }}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">To</label>
                    <input type="email" name="to_addr" class="form-control" value="{{ to_addr }}" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">Subject</label>
                    <input type="text" name="subject" class="form-control" value="{{ subject }}">
                </div>
                <div class="mb-3">
                    <label class="form-label">Body</label>
                    <textarea name="body" rows="5" class="form-control">{{ body }}</textarea>
                </div>
                <button type="submit" class="btn btn-primary">Send Email</button>
            </form>
            {% if message %}
            <hr>
            <div class="alert alert-info mt-3">{{ message }}</div>
            {% endif %}
        </div>
    </div>
</div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    message = ""
    form_data = dict(
        server="",
        port="",
        encryption="none",
        skip_auth=False,
        username="",
        password="",
        from_addr="",
        to_addr="",
        subject="Test Email",
        body="This is a test email."
    )

    if request.method == 'POST':
        form_data.update({
            'server': request.form.get('server', ''),
            'port': request.form.get('port', ''),
            'encryption': request.form.get('encryption', 'none'),
            'skip_auth': request.form.get('skip_auth') == 'skip',
            'username': request.form.get('username', ''),
            'password': request.form.get('password', ''),
            'from_addr': request.form.get('from_addr', ''),
            'to_addr': request.form.get('to_addr', ''),
            'subject': request.form.get('subject', 'Test Email'),
            'body': request.form.get('body', 'This is a test email.'),
        })

        server = form_data['server']
        port = int(form_data['port']) if form_data['port'] else 0
        encryption = form_data['encryption']
        skip_auth = form_data['skip_auth']
        username = form_data['username'] if not skip_auth else ''
        password = form_data['password'] if not skip_auth else ''
        from_addr = form_data['from_addr']
        to_addr = form_data['to_addr']
        subject = form_data['subject']
        body = form_data['body']

        message_obj = MIMEMultipart()
        message_obj['From'] = from_addr
        message_obj['To'] = to_addr
        message_obj['Subject'] = subject
        message_obj.attach(MIMEText(body, 'plain'))

        try:
            print(f"Connecting to SMTP server {server}:{port} with encryption {encryption}")
            if encryption == 'ssl':
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(server, port, context=context, timeout=10) as smtp:
                    smtp.set_debuglevel(1)
                    if username:
                        print("Logging in...")
                        smtp.login(username, password)
                    smtp.sendmail(from_addr, to_addr, message_obj.as_string())
                    print("Email sent successfully.")
            else:
                with smtplib.SMTP(server, port, timeout=10) as smtp:
                    smtp.set_debuglevel(1)
                    if encryption == 'starttls':
                        print("Starting TLS...")
                        smtp.starttls()
                    if username:
                        print("Logging in...")
                        smtp.login(username, password)
                    smtp.sendmail(from_addr, to_addr, message_obj.as_string())
                    print("Email sent successfully.")
            message = "✅ Email sent successfully."
        except smtplib.SMTPAuthenticationError:
            message = "❌ Authentication failed. Please check your username/password."
            print("SMTPAuthenticationError")
        except (smtplib.SMTPConnectError, socket.gaierror, socket.timeout) as e:
            message = "❌ Could not connect to the SMTP server. Please verify server address and port."
            print("Connection error:", e)
        except smtplib.SMTPRecipientsRefused as e:
            message = "❌ Recipient address rejected by the SMTP server."
            print("Recipient refused:", e)
        except Exception as e:
            message = f"❌ Error: {str(e)}"
            print("Unexpected error:", e)

    return render_template_string(HTML_FORM, message=message, **form_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)


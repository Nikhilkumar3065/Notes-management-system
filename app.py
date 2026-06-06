from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3
import os
import re
from werkzeug.security import generate_password_hash, check_password_hash
import smtplib
from email.mime.text import MIMEText
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = "@#$ni@#mjh#hhnj@9*&#$"  # Change this to a random secret key in production
serializer = URLSafeTimedSerializer(app.secret_key)
# ---------------- DATABASE CONNECTION ----------------

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "notes.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn
# ---------------- HOME ----------------

@app.route('/')
def home():
    return redirect(url_for('login'))

# ---------------- ABOUT ----------------

@app.route('/about')
def about():
    return render_template('about.html')

# ---------------- CONTACT ----------------

@app.route('/testmail')
def testmail():

    try:

        msg = MIMEText("Testing Gmail SMTP")

        msg["Subject"] = "SMTP Test"
        msg["From"] = SENDER_EMAIL
        msg["To"] = SENDER_EMAIL

        server = smtplib.SMTP(
            SMTP_SERVER,
            SMTP_PORT
        )

        server.starttls()

        server.login(
            SENDER_EMAIL,
            SENDER_PASSWORD
        )

        server.sendmail(
            SENDER_EMAIL,
            SENDER_EMAIL,
            msg.as_string()
        )

        server.quit()

        return "EMAIL SENT SUCCESSFULLY"

    except Exception as e:

        return str(e)
#-----------search engine optimization (SEO)----------------
@app.route('/search', methods=['POST'])
def search():

    if 'user_id' not in session:
        return redirect('/login')

    keyword = request.form['keyword']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM notes
        WHERE user_id= ?
        AND (title LIKE ? OR content LIKE ?)    
    """, (
        session['user_id'],
        f"%{keyword}%",
        f"%{keyword}%"
    ))

    notes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'search_results.html',
        notes=notes,
        keyword=keyword
    )


# ---------- CONFIG (Gmail SMTP example) ----------
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "kumarnk3065@gmail.com"
SENDER_PASSWORD = "ywca cjim phtv dnuq"   # ⚠️ use App Password (not normal password)
RECEIVER_EMAIL = "kumarnk3065@gmail.com"


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        # Email body content
        body = f"""
You have received a new message from Contact Form:

Name: {name}
Email: {email}
Subject: {subject}

Message:
{message}
        """

        try:
            # Create email message
            msg = MIMEText(body)
            msg["Subject"] = subject if subject else "New Contact Form Message"
            msg["From"] = SENDER_EMAIL
            msg["To"] = RECEIVER_EMAIL

            # Connect to SMTP server
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()  # secure connection
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            # Send email
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            server.quit()

            flash("Message sent successfully!", "success")
            return redirect("/contact")

        except Exception as e:
            print("CONTACT ERROR:", repr(e))
            flash(f"Error: {str(e)}", "danger")
            return redirect("/contact")

    return render_template("contact.html")


# ---------------- REGISTER ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if not username or not email or not password:
            flash("All fields are required", "danger")
            return redirect('/register')

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username= ? OR email= ?",
            (username, email)
        )

        existing_user = cur.fetchone()

        if existing_user:
            flash("Username or Email already exists", "danger")
            cur.close()
            conn.close()
            return redirect('/register')

        cur.execute(
            "INSERT INTO users(username,email,password) VALUES(?,?,?)",
            (username, email, hashed_password)
        )

        conn.commit()

        cur.close()
        conn.close()

        flash("Registration Successful", "success")
        return redirect('/login')

    return render_template('register.html')

# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username= ?",
            (username,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user['password'], password):

            session['user_id'] = user['id']
            session['username'] = user['username']

            flash("Login Successful", "success")
            return redirect('/viewall')

        flash("Invalid Username or Password", "danger")

    return render_template('login.html')

# ---------------- FORGOT PASSWORD ----------------

@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():

    if request.method == 'POST':

        email = request.form['email']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(            "SELECT * FROM users WHERE email= ?",
            (email,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user:

            flash(
                "Email Not Found",
                "danger"
            )

            return redirect('/forgotpassword')

        try:

            token = serializer.dumps(
                email,
                salt='reset-password'
            )

            reset_link = url_for(
                'resetpassword',
                token=token,
                _external=True
            )

            body = f"""
Hello {user['username']},

Click the link below to reset your password:

{reset_link}

This link expires in 30 minutes.
"""

            msg = MIMEText(body)

            msg["Subject"] = "Password Reset"
            msg["From"] = SENDER_EMAIL
            msg["To"] = email

            server = smtplib.SMTP(
                SMTP_SERVER,
                SMTP_PORT
            )

            server.starttls()

            server.login(
                SENDER_EMAIL,
                SENDER_PASSWORD
            )

            server.sendmail(
                SENDER_EMAIL,
                email,
                msg.as_string()
            )

            server.quit()

            flash(
                "Reset link sent to your email",
                "success"
            )

            return redirect('/login')

        except Exception as e:

            print("EMAIL ERROR:", str(e))

            flash(
                f"Failed to send email: {str(e)}",
                "danger"
            )

            return redirect('/forgotpassword')

    return render_template('forgotpassword.html')
# ---------------- RESET PASSWORD ----------------
@app.route('/resetpassword/<token>', methods=['GET', 'POST'])
def resetpassword(token):

    try:

        email = serializer.loads(
            token,
            salt='reset-password',
            max_age=1800
        )

    except Exception:

        flash(
            "Invalid or Expired Link",
            "danger"
        )

        return redirect('/forgotpassword')

    if request.method == 'POST':

        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:

            flash(
                "Passwords do not match",
                "danger"
            )

            return redirect(
                url_for(
                    'resetpassword',
                    token=token
                )
            )

        hashed_password = generate_password_hash(
            password
        )

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET password=? WHERE email= ?",
            (hashed_password, email)
        )

        conn.commit()

        cur.close()
        conn.close()

        flash(
            "Password Updated Successfully",
            "success"
        )

        return redirect('/login')

    return render_template('resetpassword.html')

# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():

    session.clear()

    flash("Logged Out Successfully", "info")

    return redirect('/login')

# ---------------- ADD NOTE ----------------

@app.route('/addnote', methods=['GET', 'POST'])
def addnote():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        title = request.form['title']
        content = request.form['content']

        user_id = session['user_id']

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO notes(title,content,user_id) VALUES(?,?,?)",
            (title, content, user_id)
        )

        conn.commit()

        cur.close()
        conn.close()

        flash("Note Added Successfully", "success")

        return redirect('/viewall')

    return render_template('addnote.html')

# ---------------- VIEW ALL NOTES ----------------

@app.route('/viewall')
def viewall():

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM notes WHERE user_id=? ORDER BY created_at DESC",
        (user_id,)
    )

    notes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        'viewnotes.html',
        notes=notes
    )

# ---------------- VIEW SINGLE NOTE ----------------

@app.route('/viewnotes/<int:note_id>')
def viewnotes(note_id):

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM notes WHERE id=? AND user_id=?",
        (note_id, user_id)
    )

    note = cur.fetchone()

    cur.close()
    conn.close()

    if not note:
        flash("Note Not Found", "danger")
        return redirect('/viewall')

    return render_template(
        'singlenote.html',
        note=note
    )

# ---------------- UPDATE NOTE ----------------

@app.route('/updatenote/<int:note_id>', methods=['GET', 'POST'])
def updatenote(note_id):

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM notes WHERE id=? AND user_id=?",
        (note_id, user_id)
    )

    note = cur.fetchone()

    if not note:

        cur.close()
        conn.close()

        flash("Note Not Found", "danger")

        return redirect('/viewall')

    if request.method == 'POST':

        title = request.form['title']
        content = request.form['content']

        cur.execute(
            "UPDATE notes SET title=?, content=? WHERE id=? AND user_id=?",
            (title, content, note_id, user_id)
        )

        conn.commit()

        cur.close()
        conn.close()

        flash("Note Updated Successfully", "success")

        return redirect('/viewall')

    cur.close()
    conn.close()

    return render_template(
        'updatenote.html',
        note=note
    )

# ---------------- DELETE NOTE ----------------

@app.route('/deletenote/<int:note_id>', methods=['POST'])
def deletenote(note_id):

    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM notes WHERE id=? AND user_id=?",
        (note_id, user_id)
    )

    conn.commit()

    cur.close()
    conn.close()

    flash("Note Deleted Successfully", "info")

    return redirect('/viewall')

# ---------------- RUN APP ----------------

if __name__ == '__main__':
    app.run(debug=False)
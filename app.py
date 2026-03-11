from flask import Flask, render_template, request, redirect, session, flash
import re
import psycopg2
import re
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = "secretkey123"


def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="my_app",
        user="postgres",
        password="251105"
    )
    return conn


@app.route("/")
def index():
    return render_template("index.html")


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    # Tambahan: bersihkan session saat akses halaman login (GET)
    if request.method == "GET":
        session.pop("user", None)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username:
            flash("Username belum dimasukkan")
            return redirect("/login")

        if not password:
            flash("Password belum dimasukkan")
            return redirect("/login")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user:
            flash("Akun belum terdaftar")
            return redirect("/login")

        if user[1] != password:
            flash("Password salah")
            return redirect("/login")

        session["user"] = user[0]
        return redirect("/dashboard")

    return render_template("login.html")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "dashboard.html",
        username=session["user"],
        total_users=total_users
    )


# ================= REGISTER =================
# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        session.pop("user", None)
        return render_template("register.html")

    # ================= POST =================
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "").strip()

    if not username or not password:
        flash("Semua field wajib diisi")
        return redirect("/register")

    if not re.match(r"^[A-Za-z0-9_]{3,20}$", username):
        flash("Username hanya boleh huruf, angka, dan underscore (3-20 karakter)")
        return redirect("/register")

    if len(password) < 8:
        flash("Password minimal 8 karakter")
        return redirect("/register")

    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        flash("Password harus kombinasi huruf dan angka")
        return redirect("/register")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            flash("Username sudah terdaftar")
            cur.close()
            conn.close()
            return redirect("/register")

        hashed_password = generate_password_hash(password)

        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()

        cur.close()
        conn.close()

        flash("Registrasi berhasil! Silakan login.")
        return redirect("/login")

    except Exception:
        flash("Terjadi kesalahan pada sistem. Coba lagi.")
        return redirect("/register")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")   # ke halaman utama

if __name__ == "__main__":
    app.run(debug=True)
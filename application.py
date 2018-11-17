import os, urllib.parse, requests, json

from flask import Flask, session, render_template, request, redirect, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from helpers import *

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("homepage.html")

@app.route("/login_requests", methods=["POST"])
def process_login_request():
    username = request.form.get("username")
    password = hash(request.form.get("password"))

    user = db.execute("SELECT * FROM users WHERE username = :username", {"username":username}).fetchone()

    if user is None:
        return render_template("login.html", has_error=True, error="User does not exist")
    elif int(user["password"]) != int(password):
        return render_template("login.html", has_error=True, error="Incorrect password")
    else:
        session["user"] = user
        return redirect("/dashboard")

    return redirect("/")

@app.route("/register_requests", methods=["POST"])
def process_register_request():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm = request.form.get("confirm-password")
    agreed = request.form.get("terms-of-service")

    if not agreed:
        return render_template("register.html", has_error=True, error="Please agree to our terms of service")

    if not password == confirm:
        return render_template("register.html", has_error=True, error="Passwords must match")
    
    # Check to see if user already exists
    old_user = db.execute("SELECT * FROM users WHERE username = :username", {"username":username}).fetchone()
    if not old_user is None:
        return render_template("register.html", has_error=True, error="That username is already taken")

    hashed = hash(password)
    db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username":username, "password":hashed})
    db.commit()
    user = db.execute("SELECT * FROM users WHERE username = :username", {"username":username}).fetchone()
    session["user"] = user
    return redirect("/dashboard")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", username=session["user"]["username"], classes=session["user"]["classes"])

@app.route("/logout")
def logout():
    session["username"] = None
    return redirect("/")

@app.route("/termsofservice")
def tos():
    return "They don't exist just please don't sue us."

if __name__ == "__main__":
    threading.Thread(target=app.run).start()

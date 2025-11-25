from flask import Flask, render_template, request, redirect, url_for, session, flash
from routes.auth import auth_bp
from database.db import get_db, close_db
from database.models import init_tables

import pickle
import os
from cryptography.fernet import Fernet
import pandas as pd
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "your-very-secure-secret-key"

# -----------------------------
# REGISTER BLUEPRINTS
# -----------------------------
app.register_blueprint(auth_bp)


# -----------------------------
# DATABASE INIT
# -----------------------------
@app.before_request
def create_tables():
    if not hasattr(app, 'db_initialized'):
        db = get_db()
        init_tables(db)
        app.db_initialized = True


@app.teardown_appcontext
def shutdown_session(exception=None):
    close_db()


# -----------------------------
# LOAD ML MODEL
# -----------------------------
ELIGIBILITY_MODEL_PATH = "models/eligibility_model.pkl"

try:
    eligibility_model = pickle.load(open(ELIGIBILITY_MODEL_PATH, "rb"))
except:
    eligibility_model = None
    print("⚠ WARNING: No ML model found. Running in demo mode.")


# -----------------------------
# ENCRYPTION SETUP
# -----------------------------
KEY_PATH = "utils/secret.key"

if os.path.exists(KEY_PATH):
    with open(KEY_PATH, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)

cipher = Fernet(key)

def encrypt_value(value):
    return cipher.encrypt(str(value).encode())

def decrypt_value(token):
    return cipher.decrypt(token).decode()


# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html", username=session.get("username"))


# -----------------------------------------
# ZAKAT ELIGIBILITY
# -----------------------------------------
@app.route("/eligibility", methods=["GET", "POST"])
def eligibility():
    result = None

    if request.method == "POST":
        try:
            income = float(request.form["income"])
            savings = float(request.form["savings"])
            gold_grams = float(request.form["gold"])   # gold in grams
            debts = float(request.form["debts"])

            # Encrypt
            enc_income = encrypt_value(income)
            enc_savings = encrypt_value(savings)

            # Machine Learning Prediction
            if eligibility_model:
                features = [[income, savings, gold_grams, debts]]
                prediction = eligibility_model.predict(features)[0]

                if prediction == 1:
                    result = "Zakat is Required"
                else:
                    result = "Zakat is Not Required"
            else:
                result = "ML Model Missing – Demo Result Only"

        except Exception as e:
            result = f"Error: {e}"

    return render_template("eligibility.html", result=result)


# -----------------------------------------
# FORECAST GRAPH
# -----------------------------------------
@app.route("/forecast", methods=["GET", "POST"])
def forecast():
    graph = None

    if request.method == "POST":
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        income = [2000, 2100, 2200, 2300, 2400, 2550]

        plt.figure(figsize=(6,4))
        plt.plot(months, income, linewidth=3)
        plt.title("6-Month AI Forecast", fontsize=14)
        plt.xlabel("Month")
        plt.ylabel("Income (€)")

        png = io.BytesIO()
        plt.savefig(png, format="png", bbox_inches="tight")
        png.seek(0)
        graph = base64.b64encode(png.getvalue()).decode()

    return render_template("forecast.html", graph=graph)


# -----------------------------------------
# DONATION PAGE (DEMO)
# -----------------------------------------
@app.route("/donate", methods=["GET", "POST"])
def donate():
    confirmation = None

    if request.method == "POST":
        charity = request.form.get("charity")
        amount = request.form.get("amount")

        confirmation = f"You successfully donated €{amount} to {charity} (Demo Mode)."

    return render_template("donate.html", confirmation=confirmation)


# -----------------------------------------
# LOGOUT
# -----------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


if __name__ == "__main__":
    app.run(debug=True)

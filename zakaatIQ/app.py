from flask import Flask, render_template, request, redirect, url_for, session, flash
import pickle
import os
from cryptography.fernet import Fernet
import pandas as pd
import base64
import io
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = "your-very-secure-secret-key"

# -----------------------------
# Load ML Model
# -----------------------------
ELIGIBILITY_MODEL_PATH = "models/eligibility_model.pkl"

try:
    eligibility_model = pickle.load(open(ELIGIBILITY_MODEL_PATH, "rb"))
except:
    eligibility_model = None
    print("⚠ WARNING: No ML model found. Running in demo mode.")


# -----------------------------
# Encryption Setup
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

# -----------------------------------------
# HOMEPAGE (Islamic Landing Page)
# -----------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------------------
# LOGIN
# -----------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    """ Simple demo login """
    if request.method == "POST":
        email = request.form.get("email")
        session["user"] = email
        return redirect(url_for("dashboard"))

    return render_template("login.html")


# -----------------------------------------
# DASHBOARD (requires login)
# -----------------------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")


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

            # Encrypt (demo only)
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
# FORECAST GRAPH (DEMO)
# -----------------------------------------
@app.route("/forecast", methods=["GET", "POST"])
def forecast():
    graph = None

    if request.method == "POST":
        months = [1, 2, 3, 4, 5, 6]
        income = [2000, 2200, 2100, 2300, 2400, 2500]

        plt.figure(figsize=(6, 4))
        plt.plot(months, income)
        plt.title("Income Trend (Demo)")
        plt.xlabel("Month")
        plt.ylabel("Income (€)")

        png = io.BytesIO()
        plt.savefig(png, format="png")
        png.seek(0)
        graph = base64.b64encode(png.getvalue()).decode()

    return render_template("forecast.html", graph=graph)


# -----------------------------------------
# DONATION PAGE
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
    return redirect(url_for("login"))


# -----------------------------------------
# RUN APP
# -----------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, session
from routes.auth import auth_bp
from database.db import get_db, close_db
from database.models import init_tables

app = Flask(__name__)
app.secret_key = "super_secret_key"  # Replace later - load from env

# Register Blueprint
app.register_blueprint(auth_bp)

# DATABASE INIT
@app.before_first_request
def create_tables():
    db = get_db()
    init_tables(db)

@app.teardown_appcontext
def close_connection(exception):
    close_db()

# HOME
@app.route('/')
def home():
    return render_template('index.html')

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template("dashboard.html", username=session['username'])

if __name__ == "__main__":
    app.run(debug=True)

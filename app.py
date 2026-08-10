from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
import os

app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your_secret_key'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# -------------------------
# User Database Model
# -------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)


# Create database tables if they don't exist
with app.app_context():
    db.create_all()


# -------------------------
# Load Machine Learning Model
# -------------------------
print("📁 Files in model/:", os.listdir("model"))

model_data = joblib.load("model/retrained_model.pkl")

model = model_data['model']
columns = model_data['columns']


# -------------------------
# Register
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form['email']
        password = request.form['password']

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return render_template("register.html")

        # Hash password
        hashed_pw = generate_password_hash(password)

        # Create new user
        new_user = User(
            email=email,
            password=hashed_pw
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.")

        return redirect(url_for("login"))

    return render_template("register.html")


# -------------------------
# Login
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session['user'] = email

            return redirect(url_for("predict_form"))

        else:
            flash("Password or Email invalid.")

    return render_template("login.html")


# -------------------------
# Logout
# -------------------------
@app.route("/logout")
def logout():

    session.pop('user', None)

    return redirect(url_for("login"))


# -------------------------
# Home
# -------------------------
@app.route("/")
def home():

    return redirect(url_for("login"))


# -------------------------
# Prediction + Feedback
# -------------------------
@app.route("/predict_form", methods=["GET", "POST"])
def predict_form():

    # Check whether user is logged in
    if 'user' not in session:
        return redirect(url_for("login"))

    prediction = None
    message = None

    # -------------------------
    # Crop Yield Prediction
    # -------------------------
    if request.method == "POST" and 'predict' in request.form:

        data = {
            "rainfall_mm": float(request.form['rainfall_mm']),
            "soil_quality_index": float(request.form['soil_quality_index']),
            "farm_size_hectares": float(request.form['farm_size_hectares']),
            "sunlight_hours": float(request.form['sunlight_hours']),
            "fertilizer_kg": float(request.form['fertilizer_kg'])
        }

        # Convert input to DataFrame
        df = pd.DataFrame([data])

        # Match the columns used during model training
        df = df.reindex(columns=columns, fill_value=0)

        # Make prediction
        prediction = model.predict(df)[0]


    # -------------------------
    # Feedback
    # -------------------------
    if request.method == "POST" and 'feedback' in request.form:

        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        feedback_data = pd.DataFrame(
            [[name, email, message]],
            columns=["name", "email", "message"]
        )

        file_exists = os.path.exists("feedback.csv")

        feedback_data.to_csv(
            "feedback.csv",
            mode='a',
            index=False,
            header=not file_exists
        )

        message = "✅ Feedback submitted!"

    return render_template(
        "index.html",
        prediction=prediction,
        message=message
    )


# -------------------------
# Run Application
# -------------------------
if __name__ == '__main__':

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )

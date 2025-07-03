from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)

print("📁 Files in model/:", os.listdir("model"))


model_data = joblib.load("model/retrained_model.pkl")
model = model_data['model']
columns = model_data['columns']


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(email=email, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful. Please log in.")
            return redirect(url_for("login"))
    return render_template("register.html")

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

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for("login"))

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/predict_form", methods=["GET", "POST"])
def predict_form():
    if 'user' not in session:
        return redirect(url_for("login"))

    prediction = None
    message = None

    if request.method == "POST" and 'predict' in request.form:
        data = {
            "rainfall_mm": float(request.form['rainfall_mm']),
            "soil_quality_index": float(request.form['soil_quality_index']),
            "farm_size_hectares": float(request.form['farm_size_hectares']),
            "sunlight_hours": float(request.form['sunlight_hours']),
            "fertilizer_kg": float(request.form['fertilizer_kg'])
        }
        df = pd.DataFrame([data])
        df = df.reindex(columns=columns, fill_value=0)
        prediction = model.predict(df)[0]

    if request.method == "POST" and 'feedback' in request.form:
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        feedback_data = pd.DataFrame([[name, email, message]], columns=["name", "email", "message"])
        file_exists = os.path.exists("feedback.csv")
        feedback_data.to_csv("feedback.csv", mode='a', index=False, header=not file_exists)
        message = "✅ Feedback submitted!"

    return render_template("index.html", prediction=prediction, message=message)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=1234)
import numpy as np
import pickle
import json
import smtplib
from flask import Flask, request, render_template, redirect, url_for, session
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a secure key in production

# Load the model
model = pickle.load(open('credit.pkl', 'rb'))

# Email configurations
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_FROM = 'akashkalam444@gmail.com'  # Replace with your email
EMAIL_PASSWORD = 'Akash1234'  # Replace with your email app password

# Load user data
def load_user_data():
    try:
        with open('users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(users):
    with open('users.json', 'w') as f:
        json.dump(users, f)

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Default route to redirect to login page
@app.route('/')
def index():
    return redirect(url_for('login_user'))

# User dashboard
@app.route('/home')
def home():
    if 'username' in session:
        return render_template('index.html')  # Render index page after login
    return redirect(url_for('login'))  # Redirect to login if not logged in

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_user_data()
        if username in users and users[username]['password'] == password:
            session['username'] = username
            
            # Send email notification on successful login
            user_email = users[username]['email']
            send_email(user_email, "Login Notification", "You have successfully logged in.")
            
            return redirect(url_for('home'))  # Redirect to home (index page) after login
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']  # New field for email
        
        users = load_user_data()
        if username in users:
            return render_template('register.html', error='Username already exists')
        
        # Store username, password, and email
        users[username] = {'password': password, 'email': email}
        save_user_data(users)
        
        # Send welcome email
        send_email(email, "Welcome to Our Service!", "Thank you for registering!")
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))  # Redirect to login after logout

# Prediction route
@app.route('/predict', methods=['POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    features = [float(request.form.get(f'v{i}', 0)) for i in range(1, 29)]
    time = float(request.form['time'])
    amount = float(request.form['amount'])
    
    final_features = [np.array(features + [time, amount])]
    prediction = model.predict(final_features)

    # Send email notification with the prediction
    user_email = load_user_data()[session['username']]['email']
    prediction_result = "Not Fraud" if prediction[0] == 1 else "Fraud"  # Adjust based on your prediction logic
    send_email(user_email, "Prediction Result", f'The Prediction for your transaction is: {prediction_result}')

    return render_template('result.html', prediction_text='The transaction is classified as: {}'.format(prediction_result), prediction=prediction)

if __name__ == "__main__":
    app.run(debug=True)

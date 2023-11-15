from flask import Flask, render_template, redirect, request, session
import pymysql

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Database Configuration (MySQL)
# Replace 'your_db_config' with your actual MySQL configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'user_service_db'

connection = pymysql.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB'],
    cursorclass=pymysql.cursors.DictCursor
)

# Function to get the welcome message based on user's role (customize as needed)
def get_welcome_message(username):
    # Example: If the username is 'admin', return 'Welcome Admin', else return a generic message
    if username.lower() == 'admin':
        return 'Welcome Admin'
    else:
        return 'Welcome'

# Route for the root path
@app.route('/')
def index():
    # Redirect to the /users route
    return redirect('/users')

# Route for the login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with connection.cursor() as cursor:
            # Check if the user exists
            cursor.execute("SELECT * FROM user WHERE username=%s AND password=%s", (username, password))
            user = cursor.fetchone()

        if user:
            # User found, set session and redirect to user management
            session['user_id'] = user['id']
            return redirect('/user_management')
        else:
            # User not found, show login page with an error message
            return render_template('login.html', error='Invalid credentials')

    # If it's a GET request, show the login page
    return render_template('login.html', error=None)

# Route for the signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with connection.cursor() as cursor:
            # Check if the username is already taken
            cursor.execute("SELECT * FROM user WHERE username=%s", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                # Username already taken, show signup page with an error message
                return render_template('signup.html', error='Username already taken')

            # Create a new user
            cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, password))
            connection.commit()

            # Log in the new user and redirect to user management
            cursor.execute("SELECT * FROM user WHERE username=%s", (username,))
            new_user = cursor.fetchone()
            session['user_id'] = new_user['id']
            return redirect('/user_management')

    # If it's a GET request, show the signup page
    return render_template('signup.html', error=None)

# Route for user management page
@app.route('/user_management')
def user_management():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM user WHERE id=%s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return redirect('/login')

        # Fetch other users for display
        cursor.execute("SELECT * FROM user WHERE id != %s", (user_id,))
        users = cursor.fetchall()

    return render_template('user_management.html', user=user, users=users)

# Route for juice billing page
@app.route('/juice_billing')
def juice_billing():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM user WHERE id=%s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return redirect('/login')

    # Fetch the welcome message from user_service
    welcome_message = get_welcome_message(user['username'])

    # Redirect to Juice Billing service on a different port
    return redirect(f'http://127.0.0.1:5001/?user_id={user_id}&welcome_message={welcome_message}')

# Route for logging out
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)

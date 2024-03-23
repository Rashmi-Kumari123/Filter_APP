############################ Importing required module and packages #########################

import os
from flask import Flask, render_template, request, flash, redirect, url_for, session
from werkzeug.utils import secure_filename 
from PIL import Image
import cv2
import numpy as np 
import psycopg2
############################## Database Connection #######################################
database_url = "dpg-cnvc5t6ct0pc73dmc3ng-a.oregon-postgres.render.com"
host = f"{database_url}"


def connect_db():
    conn = psycopg2.connect(
        dbname="filter_app",
        user="filter_app_user",
        password="c9me2zEZMvl7e4ZzpDVEQBl5ioHSrpyD",
        host=host
    )
    return conn

conn = connect_db()
cur = conn.cursor()

# Create the users table if it doesn't exist
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
""")
conn.commit()

##################### Upload Allowed Extension ##########################################

UPLOAD_FOLDER = 'static'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

app = Flask(__name__)
app.secret_key = "super secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


############################## Filter Processing #####################################

def ProcessImage(filename, operation, **kwargs):
    print(f"the operation is {operation} and file name is {filename}")
    img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(img_path):
        flash("Uploaded file does not exist.")
        return None

    img = cv2.imread(img_path)

    if operation == "cgray":
        imgProcessed = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        newfilename = f'{filename.split(".")[0]}_cgray.jpg'
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], newfilename), imgProcessed)
        return newfilename

    elif operation == 'crop':
        x, y, w, h = kwargs.get('x'), kwargs.get('y'), kwargs.get('w'), kwargs.get('h')
        cropped_img = img[y:y+h, x:x+w]
        newfilename = f'{filename.split(".")[0]}_crop.jpg'
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], newfilename), cropped_img)
        return newfilename

    elif operation == 'rotate':
        angle = kwargs.get('angle')
        (h, w) = img.shape[:2]
        center = (w / 2, h / 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated_img = cv2.warpAffine(img, M, (w, h))
        newfilename = f'{filename.split(".")[0]}_rotate.jpg'
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], newfilename), rotated_img)
        return newfilename
    
    elif operation == 'blur':
        blur_amount = kwargs.get('blur_amount')
        if blur_amount % 2 == 0:
            blur_amount += 1  # Ensure blur_amount is odd
        blur_amount = max(1, blur_amount)  # Ensure blur_amount is at least 1
        blurred_img = cv2.GaussianBlur(img, (blur_amount, blur_amount), 0)
        newfilename = f'{filename.split(".")[0]}_blur.jpg'
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], newfilename), blurred_img)
        return newfilename
    elif operation == 'cool':
        cool_img = cv2.applyColorMap(img, cv2.COLORMAP_COOL)
        newfilename = f'{filename.split(".")[0]}_cool.jpg'
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], newfilename), cool_img)
        return newfilename
    
    elif operation == 'vintage':
        kernel = np.array([[0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 1, 0, 0],
                        [0, 0, 0, 0, 0],
                        [0, 0, 0, 0, 0]])

        vintage_img = cv2.filter2D(img, -1, kernel)
        newfilename = f'{filename.split(".")[0]}_vintage.jpg'
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], newfilename), vintage_img)
        return newfilename

    elif operation == 'brightness':
        brightness_factor = kwargs.get('brightness_factor')
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.add(v, brightness_factor)
        brightness_adjusted_img = cv2.merge((h, s, v))
        newfilename = f'{filename.split(".")[0]}_brightness.jpg'
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], newfilename), cv2.cvtColor(brightness_adjusted_img, cv2.COLOR_HSV2BGR))
        return newfilename

    elif operation == 'saturation':
        saturation_factor = kwargs.get('saturation_factor')
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.add(s, saturation_factor)
        saturation_adjusted_img = cv2.merge((h, s, v))
        newfilename = f'{filename.split(".")[0]}_saturation.jpg'
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], newfilename), cv2.cvtColor(saturation_adjusted_img, cv2.COLOR_HSV2BGR))
        return newfilename
    else:
        return None
    
############################ Routing and Rendering ################################################
    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username already exists
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Username already taken')
        else:
            # Insert the new user into the database
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            flash('Account created successfully! Please log in.')
            return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the username and password are correct
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()

        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route("/")
def home():
    if 'logged_in' in session:
        return render_template("index.html", username = session['username'])
    else:
        return redirect(url_for('signup'))

    # return redirect("signup.html")

@app.route("/logout", methods=['GET', 'POST'])
def logout():
    # Clear the session
    session.pop('logged_in', None)
    session.pop('username', None)
    # Redirect to the login page
    return redirect(url_for('login'))


###################################### Editing ####################################

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == "POST":
        operation = request.form.get("operation")
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Ensure the upload directory exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            try:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                flash(f"Error saving file: {str(e)}")
                return redirect(request.url)
            
            kwargs = {}
            for param in request.form:
                if param != "operation":
                    value = request.form.get(param)
                    if value:
                        kwargs[param] = int(value)
                    else:
                        kwargs[param] = 0  # Set default value if empty
            # Provide default values for parameters if not provided
            if operation in ['crop', 'rotate', 'blur', 'brightness', 'saturation']:
                if 'blur_amount' not in kwargs:
                    kwargs['blur_amount'] = 1  # Default blur amount
            new = ProcessImage(filename, operation, **kwargs)
            if new:
                # flash(f"Your image has been processed and is available <a href='{url_for('static', filename=new)}' target='_blank'>here</a>")
                flash(f"<span style='color: green;'>Your image has been processed and is available</span> <a href='{url_for('static', filename=new)}' ><span style='color: red;'>here</span></a>")
                return render_template("index.html")
            else:
                flash("Invalid operation")
                return render_template("index.html")

    return render_template("index.html")
       
if __name__ == '__main__':
    app.run(debug=True,host = '0.0.0.0')

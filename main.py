from flask import (Flask, render_template, request,url_for, flash,redirect)
from flask_wtf import FlaskForm
import pickle
import numpy as np
from keras.preprocessing.image import load_img, img_to_array
from PIL import Image
from joblib import dump, load
import os
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

app = Flask(__name__, template_folder='venv/templates')

app.config['UPLOAD_FOLDER'] = 'venv/uploaded'
app.config['SECRET_KEY'] = 'your_secret_key'

model1 = load(open("venv/your_model_pickle1.pkl", "rb"))#300 mb
model2 = load(open("venv/your_model_pickle3.pkl", "rb"))# 500

def preprocess_image(img):
    x = np.array(img.resize((128, 128)))
    x = x.reshape(1, 128, 128, 3)
    return x

def map_label(val):
    lbl_encoding = {0: 'glioma_tumor', 1: 'meningioma_tumor', 2: 'no_tumor', 3: 'pituitary_tumor'}
    return lbl_encoding.get(val, 'Unknown')

def preprocess_image1(image_path):  # Accepts a file path
    img = load_img(image_path, target_size=(150, 150))
    img = img_to_array(img)
    img = img / 255.0
    img = np.expand_dims(img, axis=0)
    return img

app.secret_key="4949asdklfjasdklflaksdf"

app.config['MYSQL_HOST']="localhost"
app.config['MYSQL_USER']="root"
app.config['MYSQL_PASSWORD']="P@van678"
app.config['MYSQL_DB']="brain_database"

mysql=MySQL(app)
login_manage=LoginManager()
login_manage.init_app(app)
bcrypt =Bcrypt(app)

@login_manage.user_loader
def load_user(user_id):
    return User.get(user_id)

class User(UserMixin):
    def __init__(self,user_id,username,email):
        self.id=user_id
        self.name=username
        self.email=email
    @staticmethod
    def get(user_id):
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT name,email from users where id =%s',(user_id,))
        result=cursor.fetchone()
        cursor.close()
        if result:
            return User(user_id,result[0],result[1])


@app.route('/')
def index():
    return render_template('index.html')
@app.route('/reg')
def reg():
    return render_template('register.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT  INTO users (name,email,password) values(%s,%s,%s)', (username, email, hashed_password))
        mysql.connection.commit()
        cursor.close()
        flash('Successfully registered!', 'success')
        return redirect(url_for('register_success'))
    else:
        return render_template('register.html')
@app.route('/register_success')
def register_success():
    return render_template('register_success.html')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Fetch user data from the database
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT id, name, email, password FROM users WHERE name = %s', (username,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data:
            # Verify password hash
            if bcrypt.check_password_hash(user_data[3], password):
                # Create a User object
                user = User(user_data[0], user_data[1], user_data[2])
                login_user(user)
                # Redirect to the dashboard page
                return redirect(url_for('success'))
            else:
                flash('Invalid username or password', 'error')
        else:
            flash('User not found', 'error')

    # If login fails, render the login page again
    return render_template('index.html')
@app.route('/success')
def success():
    return render_template('index1.html')

@app.route('/home')
def home():
    return render_template('home.html')
@app.route('/detect_brain')
def detect_brain():
    return render_template('detect.html')

@app.route('/detect_types')
def detect_types():
    return render_template('detecttype.html')

@app.route("/detect", methods=["POST", "GET"])
def detect():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            return render_template('detect.html', yn="No selected file")
        if file:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            preprocessed_image = preprocess_image(Image.open(filename))

            res = model1.predict_on_batch(preprocessed_image)
            classification = np.where(res == np.amax(res))[1][0]

            if classification == 0:
                return render_template('detect.html', yn="you have a tumor")
            else:
                return render_template('detect.html', yn="you have no tumor")

@app.route("/detect_type", methods=["POST", "GET"])
def detect_type():
    if request.method == 'POST':
        file1 = request.files['file']
        if file1.filename == '':
            return render_template('detecttype.html', type="No selected file")
        if file1:
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
            file1.save(filename)
            preprocessed_image = preprocess_image1(filename)  # Pass the file path
            prediction = model2.predict(preprocessed_image)
            predicted_class_index = np.argmax(prediction)
            predicted_label = map_label(predicted_class_index)
            return render_template('detecttype.html', type=predicted_label)

if __name__ == '__main__':
    app.run(debug=True)
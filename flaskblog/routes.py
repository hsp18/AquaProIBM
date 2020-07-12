import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, Response
from flaskblog import app, db, bcrypt, changes, current_sensors, locateleak
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flaskblog.models import User, Post, Algorithms
from flask_login import login_user, current_user, logout_user, login_required
import json
import time
from datetime import datetime

import dropbox
import numpy as np
import cv2

def __skeletonize__(img):
    """
    :param img: input image to be skeletonized
    :return: the skeletonized mask
    """

    # create copies of the image
    img = img.copy()
    skel = img.copy()

    # extract the structural element from the image
    skel[:, :] = 0
    kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))

    while True:

        # erode and dilate the image using morphological operation
        eroded = cv2.morphologyEx(img, cv2.MORPH_ERODE, kernel)
        temp = cv2.morphologyEx(eroded, cv2.MORPH_DILATE, kernel)
        temp = cv2.subtract(img, temp)
        skel = cv2.bitwise_or(skel, temp)
        img[:, :] = eroded[:, :]
        if cv2.countNonZero(img) == 0:
            break

    return skel


"""
Find the output mask of the input image
"""
def detectCrack():
    img = cv2.imread("4.jpg")

    # blur the image and extract the edges
    blur_gray = cv2.GaussianBlur(img, (5, 5), 0)
    edges = cv2.Canny(blur_gray, 50, 150, apertureSize=3)

    # shade the border lines that are thick
    lines = cv2.HoughLinesP(image=edges, rho=1, theta=np.pi / 180, threshold=100, lines=np.array([]), minLineLength=100, maxLineGap=80)
    a, b, c = lines.shape
    for i in range(a):
        cv2.line(img, (lines[i][0][0], lines[i][0][1]), (lines[i][0][2], lines[i][0][3]), (169, 169, 169), 3,cv2.LINE_AA)

    # binarize the image after blurring
    median = cv2.medianBlur(img, 5)
    im_bw = cv2.threshold(median, 20, 255, cv2.THRESH_BINARY_INV)[1]
    gray_img = cv2.cvtColor(im_bw, cv2.COLOR_RGB2GRAY)

    # skeletonize the image and save the corresponding output
    global skel
    skel = __skeletonize__(gray_img)
    cv2.imwrite("mask2.png", skel)

    #check if there's a crack found, by checking for  pixel values
    
    #if np.amax(skel)>0:
    #    print("Crack Found")



inlet = 0
message = 0
locations = " "
posts = [
    {
        'author': 'Flowrate: Normal',
        'title': 'Flow Rate Stabilizer',
        'content': 'Master Node for data monitoring and differential stabilization.',
        'date_posted': 'Master Node'
    },
    {
        'author': 'Flowrate: Normal',
        'title': 'Leakage Prone Node',
        'content': 'Unstable due to placement near turbulent flow Source 1',
        'date_posted': 'Slave Node 1'
    }
]


@app.route("/")
def index():
    return redirect (url_for('login'))
@app.route("/home",methods=['GET','POST'])
@login_required
def home():
    #chart_data()
    global message
    global locations
    global skel
     
    dbx = dropbox.Dropbox("fg5H4EjUooAAAAAAAAAAOoipF7JBMImbX-BI5p5jqLO3KYPfoBG5CnWLjZYA2CQq")
    print("Printing the files available in dropbox root directory")
    for entry in dbx.files_list_folder('').entries:
        print(entry.name)
    print("Finished printing files from root directory of dropbox")
    
    # dbx = dropbox.Dropbox("fg5H4EjUooAAAAAAAAAAOoipF7JBMImbX-BI5p5jqLO3KYPfoBG5CnWLjZYA2CQq")
    dbx = dropbox.Dropbox("lGd216qwl2AAAAAAAAAAJKm2kPRJasllVC_xshYRfArZsOiuOGlioaVNbiSz5ekw")
    
    with open("4.jpg","wb") as f:
        metadata, res = dbx.files_download(path="/1.jpg")
        f.write(res.content)
        print("Downloaded")

    detectCrack()
    #check if there's a crack found, by checking for  pixel values
    if np.amax(skel)>0:
        print("Crack Found")
        flash("Crack Detected","danger")


    if request.method == 'POST':
        path=request.form['url']
        print("Leak in graphs")
        current_sensors['s10'] = inlet
        print('Path',path)
        loc=locateleak()
        if loc != "None":
            locations+=" "+loc
            flash('Leak Detected','danger')
            message+=1

        return redirect(path)#,msg=message)
    return render_template('home.html', msg=message,loc=locations)

@app.route('/chart-data',methods=['GET'])
def chart_data():
    def generate_random_data():
        global inlet
        for change in changes:
            if change is None or ('deleted' in change and change['deleted']):
                pass
            else:
                print(change)
                current_sensors[change['doc']['_id']] = change['doc']['value']
                index = int(change['doc']['_id'][1:]) 
                print("Index: ",index)
                json_data = json.dumps(
                    {'time':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                     'index':index,
                     'value':change['doc']['value'],
                     'values':current_sensors
                      })
                print(json_data)
                yield f"data:{json_data}\n\n"
                inlet = current_sensors['s10']
                current_sensors['s10'] = None
                #if checkleak(change['doc']):
                    
                #time.sleep(1)
    return Response(generate_random_data(), mimetype='text/event-stream')
@app.route("/about")
def about():
    return render_template('about.html', title='About',)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form,msg=message)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form,msg=message)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form,msg=message)
@app.route('/graphs',methods=['GET','POST'])
def graphs():
    global message
    if request.method == 'POST':
        path=request.form['url']
        print("Leak in graphs")
        print('Path',path)
        flash('Leak Detected','danger')
        message="Leak"

        return redirect(path)#,msg=message)

    return render_template('graphs.html',title='Graphs',msg=message)

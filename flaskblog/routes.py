import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, Response
from flaskblog import app, db, bcrypt, changes, current_sensors, locateleak
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flaskblog.models import User, Post, Algorithms, Message
from flask_login import login_user, current_user, logout_user, login_required
import json
import time
from datetime import datetime

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


@app.route('/notify/<recipient>' , methods=['POST'])
def notify(recipient):

    user = User.query.filter_by(email=recipient).first_or_404()
    print("Crack Detected")
    msg = Message(recipient=user,body=request.form['msg_from_rpi'])
    db.session.add(msg)
    db.session.commit()
    
    return {"msg":"Message sent successfully"}

@app.route('/notifications', methods=['GET'])
def notifications():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(Message.timestamp.desc()).paginate(page,2, False)
    next_url = url_for('notifications', page=messages.next_num) if messages.has_next else None
    prev_url = url_for('notifications', page=messages.prev_num) if messages.has_prev else None
    return render_template('notifications.html', messages=messages.items,next_url=next_url, prev_url=prev_url)


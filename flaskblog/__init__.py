from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from cloudant.client import Cloudant
from keras.models import load_model
import numpy as np
import tensorflow as tf
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
client = Cloudant.iam("1f2c0062-950d-4d55-912c-10495ec948e5-bluemix", "PJJTGZh1-XafDMVQ4gmohqjJbuy8mZ8sWzTc68I4WcDt")
client.connect()
my_database = client.create_database("test")
changes = my_database.changes(feed='continuous',since='now',heartbeat=5000,include_docs=True)
current_sensors = {
    's1':None,
    's2':None,
    's3':None,
    's4':None,
    's5':None,
    's6':None,
    's7':None,
    's8':None,
    's9':None,
    's10':None,
    's11':None,
    's12':None,
    }

model = load_model('./flaskblog/static/modelforui.h5')
graph = tf.get_default_graph()
#from flaskblog import routes

#def checkleak(data):
 #   inlet=data['s1']
  #  outlet=data['s3']+data['s4']+data['s5']
   # if abs(inlet-outlet) > threshold:
    #    return True
    #return False

def locateleak():
    global current_sensors
    global model
    global graph
    print("In locateleak")
    X=[]
    for i in range(1,13):
        if current_sensors['s'+str(i)] is None:
            X.append(0)
        else:
            X.append(current_sensors['s'+str(i)])
    print(X)
    print(np.abs(X))
    with graph.as_default():
        y = model.predict_classes(np.reshape(np.abs(X),(1,12)))
        print("Class:",y)
        keys = ["None","DL1","DL2","DL3","DL4","DL5","TL1","TL2"]
        current_sensors['s8']=None
        current_sensors['s10']=None
        return keys[y[0]]

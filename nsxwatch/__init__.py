from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
try:
    app.config.from_object('config')
except ImportError:
    print("Config file does not exist - please create one!")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../nsxwatch.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login = LoginManager(app)
login.login_view = 'login'
db = SQLAlchemy(app)

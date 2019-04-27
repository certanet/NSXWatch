from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.exc import OperationalError
from nsxwatch import login, db


class Setting(db.Model):
    # Contains the required settings for customising the app
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(128))
    setting_value = db.Column(db.String(128))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Edge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    edgeid = db.Column(db.String(64), index=True, unique=True)
    name = db.Column(db.String(128))
    status = db.Column(db.String(128))
    pools = db.relationship("Pool", backref="edge")

    def __init__(self, edgeid, name, status):
        self.edgeid = edgeid
        self.name = name
        self.status = status


class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    edge_id = db.Column(db.Integer, db.ForeignKey('edge.id'), nullable=False)
    poolid = db.Column(db.String(64), index=True, unique=True)
    name = db.Column(db.String(128))
    algorithm = db.Column(db.String(128))
    members = db.relationship("Member", backref="pool")
    total_sessions = db.Column(db.Integer)
    status = db.Column(db.String(128))
    current_sessions = db.Column(db.Integer)
    bytesin = db.Column(db.Integer)
    bytesout = db.Column(db.Integer)

    def __init__(self, edge_id, poolid, name, algorithm):
        self.edge_id = edge_id
        self.poolid = poolid
        self.name = name
        self.algorithm = algorithm
        self.total_sessions = 0
        self.status = 'DOWN'


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pool_id = db.Column(db.Integer, db.ForeignKey('pool.id'), nullable=False)
    memberid = db.Column(db.String(64), index=True, unique=True)
    name = db.Column(db.String(128))
    enabled = db.Column(db.Boolean)
    status = db.Column(db.String(128))
    bytesin = db.Column(db.Integer)
    bytesout = db.Column(db.Integer)
    sessions_handled = db.Column(db.Integer)
    failure_cause = db.Column(db.String(128))
    last_state_change_time = db.Column(db.String(128))

    def __init__(self, poolid, memberid, name, enabled):
        self.pool_id = poolid
        self.memberid = memberid
        self.name = name
        self.enabled = enabled
        self.status = 'DOWN'
        self.bytesin = 0
        self.bytesout = 0
        self.sessions_handled = 0

    def member_load_share(self):
        pool = Pool.query.filter_by(id=self.pool_id).first()
        load_share = calc_percent(self.sessions_handled, pool.total_sessions)
        return load_share


def get_poolkey_from_poolid(poolid):
    pool = Pool.query.filter_by(poolid=poolid).first()
    return pool.id


def calc_percent(current, total):
    if current == total:
        return 100
    try:
        return (abs(current / total) * 100)
    except ZeroDivisionError:
        return 0


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


def db_check():
    error = [False, "No issues"]
    try:
        if not User.query.all():
            error = [True, "A user has not been created"]
    except OperationalError:
        error = [True, "DB tables have not been created"]
    return error

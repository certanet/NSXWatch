from flask import render_template, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from nsxwatch import app, nsxm
from nsxwatch.models import User, db_check, Edge, Setting


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == "POST":
        attempted_username = request.form['username']
        attempted_password = request.form['password']
        user = User.query.filter_by(username=attempted_username).first()

        if user is None or not user.check_password(attempted_password):
            session['logged_in'] = False
            session['wrong_pass'] = True
            return redirect(url_for('login'))

        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Login')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/')
def index():
    if db_check()[0]:
        return render_template('error.html', error=db_check()[1])
    return render_template('index.html', title="Home")


@app.route('/loadbalancer')
@login_required
def loadbalancer():
    edges = Edge.query.all()
    stat_time = nsxm.epoch_to_human(1538218202)

    return render_template('lb3.html',
                           edges=edges,
                           stat_time=stat_time)


@app.route('/lb2')
@login_required
def lb2():
    nsx = nsxm.Nsx()
    lb_stats = nsx.getJsonPoolStats('edge-1')
    stat_time = nsxm.epoch_to_human(lb_stats['timeStamp'])

    return render_template('lb2.html',
                           lb_stats=lb_stats,
                           stat_time=stat_time)


@app.route('/blank')
def blank():
    return render_template('blank.html', title="Blank Page")


@app.route('/stats')
@login_required
def stats():
    nsx = nsxm.Nsx()
    nsxm_info = nsx.getNSXInfo()
    return render_template('stats.html',
                           title="NSXM Info",
                           nsxm_info=nsxm_info)


@app.route('/routing')
@login_required
def routing():
    return render_template('routing.html', title="Routing")


@app.route('/settings')
@login_required
def settings():
    settings = Setting().query.all()
    return render_template('settings.html',
                           title="Settings",
                           settings=settings)

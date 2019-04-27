from getpass import getpass
from nsxwatch import app, db
from nsxwatch.models import User, Setting


def main():
    with app.app_context():
        db.metadata.create_all(db.engine)
        if User.query.all():
            create = input('A user already exists! Create another? (y/n): ')
            if create == 'n':
                return

        username = input('Enter username: ')
        password = getpass('Enter password: ')
        assert password == getpass('Confirm password: ')

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print('User added!')


def add_settings():
    settings = {'nsx_user': None,
                'nsx_pass': None}

    try:
        demo = app.config['DEMO']
    except KeyError:
        demo = False

    try:
        nsx_ip = app.config['NSXM']
        settings['nsx_host'] = nsx_ip
    except KeyError:
        print("NSX not defined in config! Defaulting to DEMO mode...")
        demo = True

    settings['demo'] = demo

    if not demo:
        settings['nsx_user'] = app.config['NSX_USER']
        settings['nsx_pass'] = app.config['NSX_PASSWORD']

    for setting in settings:
        create_setting = Setting(setting_name=setting,
                                 setting_value=settings[setting])
        db.session.add(create_setting)
        db.session.commit()


if __name__ == '__main__':
    main()
    add_settings()

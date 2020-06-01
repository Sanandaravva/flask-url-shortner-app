from flask import Flask, request, render_template, redirect
from math import floor
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import Sequence
from flask_migrate import Migrate, MigrateCommand
import os

import string
try:
    from urllib.parse import urlparse  # Python 3
    str_encode = str.encode
except ImportError:
    from urlparse import urlparse  # Python 2
    str_encode = str
try:
    from string import ascii_lowercase
    from string import ascii_uppercase
except ImportError:
    from string import lowercase as ascii_lowercase
    from string import uppercase as ascii_uppercase
import base64

# Assuming urls.db is in your app root folder
app = Flask(__name__)
host = 'https://url-shortner3.herokuapp.com/'
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


def toBase62(num):
    base = string.digits + ascii_lowercase + ascii_uppercase
    r = num % 62
    res = base[r]
    q = floor(num / 62)
    while q:
        r = q % 62
        q = floor(q / 62)
        res = base[int(r)] + res
    return res


def toBase10(num):
    base = string.digits + ascii_lowercase + ascii_uppercase
    limit = len(num)
    res = 0
    for i in range(limit):
        res = 62 * res + base.find(num[i])
    return res


class Post(db.Model):
    __tablename__ = 'WEB_URL'
    id = db.Column(db.Integer(), primary_key=True)
    url = db.Column(db.LargeBinary(), unique=True)

    def __init__(self, user_url):
        self.url = base64.urlsafe_b64encode(user_url)


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        original_url = str_encode(request.form.get('url'))
        p = urlparse(original_url)
        if p.scheme == b'':
            ur = b'http://' + original_url
        else:
            ur = original_url
        pf = Post(ur)
        db.session.add(pf)
        db.session.commit()
        encoded_string = toBase62(pf.id)
        return render_template('home.html', short_url=host + encoded_string)
    return render_template('home.html')


@app.route('/<short_url>')
def redirect_short_url(short_url):
    decoded = toBase10(short_url)  # converting into decimal format
    ur = host  # fallback if no URL is found
    p = Post.query.filter_by(id=decoded).first()
    if p is not None:
        ur = base64.urlsafe_b64decode(p.url)
    return redirect(ur)


if __name__ == '__main__':
    # This code checks whether database table is created or not
    manager.run()

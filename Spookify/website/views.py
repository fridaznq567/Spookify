# this is where pages are stored

from flask import Blueprint, render_template

views = Blueprint('views', __name__)


@views.route('/')
def home():
    return render_template("home.html")


@views.route('/browse')
def browse():
    return render_template("browse.html")


@views.route('/playlist')
def playlist():
    return render_template("playlist.html")

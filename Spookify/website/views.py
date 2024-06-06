# this is where pages are stored

from flask import Blueprint

views = Blueprint('views', __name__)


@views.route('/')
def home():
    return "Hello, World!"

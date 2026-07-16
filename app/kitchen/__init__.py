from flask import Blueprint

bp = Blueprint('kitchen', __name__)

from app.kitchen import routes

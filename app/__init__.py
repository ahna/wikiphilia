# imports
from flask import Flask

# Creates our application.
app = Flask(__name__)

# Development configuration settings
# WARNING - these should not be used in production
app.config.from_pyfile('settings/development.cfg')

# Production configuration settings
# To have these override your development settings,
# you'll need to set your environment variable to
# the file path:
#export PRODUCTION_SETTINGS="/Users/ahna/Documents/Work/insightdatascience/project/wikiphilia/webapp/app/settings/production.cfg"
app.config.from_envvar('PRODUCTION_SETTINGS', silent=True)
# Application DEBUG - should be True in development
# and False in production
app.debug = app.config["DEBUG"]

# DATABASE SETTINGS
host = app.config["DATABASE_HOST"]
port = app.config["DATABASE_PORT"]
user = app.config["DATABASE_USER"]
passwd = app.config["DATABASE_PASSWORD"]
db = app.config["DATABASE_DB"]
localpath = app.config["LOCAL_PATH"]


from app import views


"""
PythonAnywhere WSGI Configuration

Copy this content to your PythonAnywhere WSGI configuration file:
/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py

Replace YOUR_USERNAME with your actual PythonAnywhere username.
"""
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/bariq'  # Change YOUR_USERNAME
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'mysql://YOUR_USERNAME:YOUR_DB_PASSWORD@YOUR_USERNAME.mysql.pythonanywhere-services.com/YOUR_USERNAME$bariq'

# Import the Flask app
from wsgi import app as application

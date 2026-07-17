"""
Reference WSGI config for PythonAnywhere.

Do NOT run this file locally. When you set up the web app on PythonAnywhere,
open the "WSGI configuration file" link in the Web tab and paste the contents
below, replacing YOURUSERNAME with your actual PythonAnywhere username.
"""

import sys

# The folder that contains app.py (adjust YOURUSERNAME).
project_home = '/home/YOURUSERNAME/EmjudeCodingTech'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# config.py calls load_dotenv(), so a .env file placed in project_home
# on PythonAnywhere will be read automatically. Keep that .env off GitHub.

from app import app as application  # noqa: E402  (PythonAnywhere looks for `application`)

# Deploying EmjudeCodingTech to PythonAnywhere

A step-by-step guide to put this Flask site live for free.

## 1. Push the latest code to GitHub
Make sure this repo (with the new `requirements.txt`) is pushed:
```bash
git push
```

## 2. Create a PythonAnywhere account
Sign up for the free "Beginner" plan at https://www.pythonanywhere.com
Your site will be live at `https://YOURUSERNAME.pythonanywhere.com`.

## 3. Open a Bash console and clone the repo
In the PythonAnywhere dashboard: **Consoles → Bash**, then:
```bash
git clone https://github.com/kingkong-nyame/emjudecodingtech.git EmjudeCodingTech
cd EmjudeCodingTech
```

## 4. Create a virtualenv and install dependencies
```bash
python3.10 --version                       # confirm a Python 3.10+ is available
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Create the .env file (secrets — never on GitHub)
Still in the Bash console:
```bash
nano .env
```
Paste this, filling in real values (use a **new** Gmail App Password):
```
SECRET_KEY=<paste output of: python -c "import secrets; print(secrets.token_hex(32))">
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=465
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-new-16-char-app-password
CONTACT_RECEIVER=where-enquiries-go@gmail.com
```
Save with `Ctrl+O`, `Enter`, then exit with `Ctrl+X`.

## 6. Initialise the database and admin user
```bash
export FLASK_APP=app.py
flask init-db          # create tables
flask seed-projects    # load the 5 showcase projects
flask create-admin     # set your admin username + password
```

## 7. Create the web app
In the dashboard: **Web → Add a new web app**
- Choose **Manual configuration** (NOT the "Flask" quickstart), same Python version as step 4.
- **Virtualenv** section → enter: `/home/YOURUSERNAME/EmjudeCodingTech/venv`
- **Code** section → set the WSGI configuration file. Click it and replace its
  contents with the contents of `wsgi_pythonanywhere.py` from this repo,
  changing `YOURUSERNAME` to your username.
- **Static files** (optional but recommended) — add:
  - URL: `/static/`  →  Directory: `/home/YOURUSERNAME/EmjudeCodingTech/static`

## 8. Reload and visit
Click the big green **Reload** button, then open
`https://YOURUSERNAME.pythonanywhere.com`.

Log in to the admin at `/admin/login` with the credentials from step 6.

## Updating the site later
```bash
cd ~/EmjudeCodingTech
git pull
source venv/bin/activate
pip install -r requirements.txt   # only if requirements changed
```
Then click **Reload** in the Web tab.

## Using your own domain (optional)
A custom domain (e.g. emjudecodingtech.com) requires the paid "Web developer"
plan on PythonAnywhere. The free plan only gives the
`YOURUSERNAME.pythonanywhere.com` address.

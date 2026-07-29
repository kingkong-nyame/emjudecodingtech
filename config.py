import os
from dotenv import load_dotenv

load_dotenv()


def _database_uri():
    """Return a SQLAlchemy-compatible database URL.

    Neon and Heroku hand out URLs using the legacy `postgres://` scheme, which
    SQLAlchemy 2.x no longer registers as a dialect. Falls back to local SQLite
    so development still works with no DATABASE_URL set.
    """
    url = os.environ.get('DATABASE_URL', 'sqlite:///emjude.db')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # On serverless hosts the container is frozen between requests and the
    # database closes idle connections, so a pooled connection can be dead by
    # the time it is reused. Verify it first and retire connections early.
    if SQLALCHEMY_DATABASE_URI.startswith('postgresql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True,
            'pool_recycle': 280,
        }

    # Flask-Mail (fill in your real credentials in .env)
    # Default to 465/SSL — port 587/STARTTLS is blocked on some networks/ISPs.
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     = int(os.environ.get('MAIL_PORT', 465))
    # TLS for 587 (STARTTLS), SSL for 465 — derived from the port unless overridden.
    MAIL_USE_SSL  = os.environ.get('MAIL_USE_SSL', str(MAIL_PORT == 465)).lower() in ('1', 'true', 'yes')
    MAIL_USE_TLS  = os.environ.get('MAIL_USE_TLS', str(MAIL_PORT == 587)).lower() in ('1', 'true', 'yes')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', '')
    CONTACT_RECEIVER    = os.environ.get('CONTACT_RECEIVER', '')

    # Site meta
    SITE_NAME  = 'EmjudeCodingTech'
    SITE_TAGLINE = 'Software Developer — Web · Mobile · APIs'
    OWNER_NAME = 'Emmanuel'
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'


class Post(db.Model):
    __tablename__ = 'posts'

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    slug       = db.Column(db.String(220), unique=True, nullable=False)
    excerpt    = db.Column(db.String(400), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    category   = db.Column(db.String(80), default='General')
    tags       = db.Column(db.String(300), default='')   # comma-separated
    published  = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    @property
    def read_time(self):
        words = len(self.body.split())
        minutes = max(1, round(words / 200))
        return f'{minutes} min read'

    def __repr__(self):
        return f'<Post {self.slug}>'


class Project(db.Model):
    __tablename__ = 'projects'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech_stack  = db.Column(db.String(300), default='')   # comma-separated
    category    = db.Column(db.String(80), default='Web') # Web | Mobile | API
    image_url   = db.Column(db.String(400), default='')
    live_url    = db.Column(db.String(400), default='')
    github_url  = db.Column(db.String(400), default='')
    featured    = db.Column(db.Boolean, default=False)
    order       = db.Column(db.Integer, default=0)
    highlights  = db.Column(db.Text, default='')          # newline-separated bullets
    icon        = db.Column(db.String(16), default='🚀')   # emoji shown on the card thumb
    thumb_color = db.Column(db.String(40), default='default')  # marketplace|jobs|medical|ecommerce|law|default
    category_label = db.Column(db.String(80), default='') # optional sub-label e.g. "Web · Marketplace"
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def stack_list(self):
        return [t.strip() for t in self.tech_stack.split(',') if t.strip()]

    @property
    def highlight_list(self):
        return [h.strip() for h in (self.highlights or '').splitlines() if h.strip()]

    @property
    def display_category(self):
        return self.category_label or self.category

    def __repr__(self):
        return f'<Project {self.title}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(200), nullable=False)
    subject    = db.Column(db.String(300), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    read       = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message from {self.email}>'
import re
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from markupsafe import escape
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message as MailMessage

from config import Config
from models import db, Admin, Post, Project, Message

# ── App factory ──────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


@app.context_processor
def inject_admin_counts():
    """Make unread_count and post_draft_count available in all admin templates."""
    counts = {}
    if current_user.is_authenticated:
        counts['unread_count']     = Message.query.filter_by(read=False).count()
        counts['post_draft_count'] = Post.query.filter_by(published=False).count()
    return counts


# ── Helpers ───────────────────────────────────────────────────────────────────

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


# ── Email rendering ─────────────────────────────────────────────────────────

# Brand palette (matches the site CSS variables).
_BRAND_NAVY    = '#0f172a'
_BRAND_SKY     = '#0284c7'
_BRAND_BORDER  = '#e2e8f0'
_BRAND_MUTED   = '#6b7280'
_BRAND_TEXT    = '#0a0a0a'


def _email_shell(inner_html):
    """Wrap content in a consistent, email-client-safe HTML shell."""
    return f"""\
<!DOCTYPE html>
<html>
  <body style="margin:0;padding:0;background:#f1f5f9;
               font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
               color:{_BRAND_TEXT};">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="background:#f1f5f9;padding:32px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="600" cellpadding="0" cellspacing="0"
                 style="max-width:600px;width:100%;background:#ffffff;border:1px solid {_BRAND_BORDER};
                        border-radius:12px;overflow:hidden;">
            <tr>
              <td style="background:{_BRAND_NAVY};padding:24px 32px;border-bottom:3px solid {_BRAND_SKY};">
                <span style="color:#ffffff;font-size:18px;font-weight:700;letter-spacing:0.3px;">
                  EmjudeCodingTech</span>
                <div style="color:#94a3b8;font-size:12px;margin-top:4px;">
                  Web &middot; Mobile &middot; APIs</div>
              </td>
            </tr>
            <tr><td style="padding:32px;">{inner_html}</td></tr>
            <tr>
              <td style="padding:18px 32px;border-top:1px solid {_BRAND_BORDER};
                         color:{_BRAND_MUTED};font-size:12px;">
                Sent automatically by the EmjudeCodingTech website.
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def render_owner_email(name, email, service_type, budget, subject, body):
    """HTML notification sent to the site owner for a new enquiry."""
    safe_email = escape(email)
    rows = [
        ('Name', escape(name)),
        ('Email', f'<a href="mailto:{safe_email}" style="color:{_BRAND_SKY};'
                  f'text-decoration:none;">{safe_email}</a>'),
        ('Service', escape(service_type)),
        ('Budget', escape(budget)),
        ('Subject', escape(subject)),
    ]
    rows_html = ''.join(
        f'<tr>'
        f'<td style="padding:8px 16px 8px 0;color:{_BRAND_MUTED};font-size:13px;'
        f'white-space:nowrap;vertical-align:top;">{label}</td>'
        f'<td style="padding:8px 0;font-size:14px;font-weight:600;">{value}</td>'
        f'</tr>'
        for label, value in rows
    )
    message_html = escape(body).replace('\n', '<br>')
    inner = f"""\
<h1 style="margin:0 0 6px;font-size:20px;color:{_BRAND_NAVY};">New contact enquiry</h1>
<p style="margin:0 0 24px;color:{_BRAND_MUTED};font-size:14px;">
  Someone reached out through the website contact form.</p>
<table role="presentation" cellpadding="0" cellspacing="0" style="width:100%;">{rows_html}</table>
<div style="margin-top:24px;padding:18px 20px;background:#f8fafc;border:1px solid {_BRAND_BORDER};
            border-radius:8px;">
  <div style="color:{_BRAND_MUTED};font-size:12px;text-transform:uppercase;
              letter-spacing:0.5px;margin-bottom:8px;">Message</div>
  <div style="font-size:15px;line-height:1.6;">{message_html}</div>
</div>
<p style="margin:24px 0 0;font-size:13px;color:{_BRAND_MUTED};">
  Reply directly to this email to respond to {escape(name)}.</p>"""
    return _email_shell(inner)


def render_autoreply_email(name, subject, body, owner):
    """HTML confirmation sent back to the person who submitted the form."""
    message_html = escape(body).replace('\n', '<br>')
    inner = f"""\
<h1 style="margin:0 0 16px;font-size:20px;color:{_BRAND_NAVY};">
  Thanks for reaching out, {escape(name)}</h1>
<p style="margin:0 0 16px;font-size:15px;line-height:1.6;">
  Your message has been received and I&rsquo;ll get back to you within 24 hours.</p>
<p style="margin:0 0 8px;color:{_BRAND_MUTED};font-size:13px;">For your records, here is what you sent:</p>
<div style="padding:18px 20px;background:#f8fafc;border-left:3px solid {_BRAND_SKY};border-radius:6px;">
  <div style="font-size:13px;color:{_BRAND_MUTED};margin-bottom:8px;">
    <strong style="color:{_BRAND_TEXT};">Subject:</strong> {escape(subject)}</div>
  <div style="font-size:15px;line-height:1.6;">{message_html}</div>
</div>
<p style="margin:24px 0 4px;font-size:15px;">Talk soon,</p>
<p style="margin:0;font-size:15px;font-weight:700;color:{_BRAND_NAVY};">{escape(owner)}</p>
<p style="margin:2px 0 0;font-size:13px;color:{_BRAND_MUTED};">EmjudeCodingTech</p>"""
    return _email_shell(inner)


# ── Public routes ─────────────────────────────────────────────────────────────

@app.route('/')
def home():
    featured_projects = Project.query.filter_by(featured=True).order_by(Project.order).limit(2).all()
    if not featured_projects:
        featured_projects = Project.query.order_by(Project.order, Project.created_at.desc()).limit(2).all()
    recent_posts      = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).limit(3).all()
    return render_template('index.html',
                           featured_projects=featured_projects,
                           recent_posts=recent_posts)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/services')
def services():
    return render_template('services.html')


@app.route('/portfolio')
def portfolio():
    category = request.args.get('category', 'all')
    if category == 'all':
        projects = Project.query.order_by(Project.order).all()
    else:
        projects = Project.query.filter_by(category=category).order_by(Project.order).all()

    counts = {
        'all':    Project.query.count(),
        'Web':    Project.query.filter_by(category='Web').count(),
        'Mobile': Project.query.filter_by(category='Mobile').count(),
        'API':    Project.query.filter_by(category='API').count(),
    }
    return render_template('portfolio.html',
                           projects=projects,
                           active_category=category,
                           counts=counts)


# ── Blog ──────────────────────────────────────────────────────────────────────

@app.route('/blog')
def blog():
    page     = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    q        = request.args.get('q', '')

    query = Post.query.filter_by(published=True)
    if category:
        query = query.filter_by(category=category)
    if q:
        query = query.filter(Post.title.ilike(f'%{q}%') | Post.excerpt.ilike(f'%{q}%'))

    posts      = query.order_by(Post.created_at.desc()).paginate(page=page, per_page=6, error_out=False)
    categories = db.session.query(Post.category).filter_by(published=True).distinct().all()
    categories = [c[0] for c in categories]

    return render_template('blog/index.html',
                           posts=posts,
                           categories=categories,
                           active_category=category,
                           search_query=q)


@app.route('/blog/<slug>')
def blog_post(slug):
    post = Post.query.filter_by(slug=slug, published=True).first_or_404()
    related = Post.query.filter(
        Post.published == True,
        Post.category == post.category,
        Post.id != post.id
    ).limit(2).all()
    return render_template('blog/post.html', post=post, related=related)


# ── Contact ───────────────────────────────────────────────────────────────────

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name         = request.form.get('name', '').strip()
        email        = request.form.get('email', '').strip()
        subject      = request.form.get('subject', '').strip()
        body         = request.form.get('body', '').strip()
        service_type = request.form.get('service_type', 'Not specified').strip()
        budget       = request.form.get('budget', 'Not specified').strip()

        if not all([name, email, subject, body]):
            flash('Please fill in all required fields.', 'error')
            return render_template('contact.html', form=request.form)

        # Save to DB
        msg = Message(name=name, email=email, subject=subject, body=body)
        db.session.add(msg)
        db.session.commit()

        # Build a rich plain-text email body
        email_body = (
            f"New contact form submission from EmjudeCodingTech\n"
            f"{'=' * 50}\n\n"
            f"Name:         {name}\n"
            f"Email:        {email}\n"
            f"Service:      {service_type}\n"
            f"Budget:       {budget}\n"
            f"Subject:      {subject}\n\n"
            f"Message:\n{body}\n\n"
            f"{'=' * 50}\n"
            f"Reply directly to: {email}\n"
        )

        # Send email notification
        receiver = app.config.get('CONTACT_RECEIVER') or app.config.get('MAIL_USERNAME')
        mail_configured = bool(
            app.config.get('MAIL_USERNAME') and
            app.config.get('MAIL_PASSWORD') and
            receiver
        )

        if mail_configured:
            try:
                mail_msg = MailMessage(
                    subject=f'[EmjudeCodingTech] {subject} — from {name}',
                    recipients=[receiver],
                    body=email_body,
                    html=render_owner_email(name, email, service_type, budget, subject, body),
                    reply_to=email,
                )
                mail.send(mail_msg)
            except Exception as e:
                # Log the real error so you can debug it
                logging.error(f'[Contact] Mail send failed: {e}')
                # Still show success to the user — message is saved in DB

            # Auto-reply confirmation to the person who reached out
            owner = app.config.get('OWNER_NAME', 'EmjudeCodingTech')
            reply_body = (
                f"Hi {name},\n\n"
                f"Thanks for reaching out to EmjudeCodingTech — your message has "
                f"landed and I'll get back to you within 24 hours.\n\n"
                f"For your records, here's what you sent:\n"
                f"{'-' * 50}\n"
                f"Subject: {subject}\n\n"
                f"{body}\n"
                f"{'-' * 50}\n\n"
                f"Talk soon,\n"
                f"{owner}\n"
                f"EmjudeCodingTech — Web · Mobile · APIs\n"
            )
            try:
                auto_reply = MailMessage(
                    subject='Thanks for contacting EmjudeCodingTech',
                    recipients=[email],
                    body=reply_body,
                    html=render_autoreply_email(name, subject, body, owner),
                    reply_to=receiver,
                )
                mail.send(auto_reply)
            except Exception as e:
                # Auto-reply is best-effort — never block the submission on it
                logging.error(f'[Contact] Auto-reply send failed: {e}')
        else:
            logging.warning('[Contact] Mail not configured — message saved to DB only.')

        flash("Message sent! I'll get back to you within 24 hours.", 'success')
        return redirect(url_for('contact'))

    return render_template('contact.html', form={})


# ── Admin: auth ───────────────────────────────────────────────────────────────

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user     = Admin.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))

        flash('Invalid username or password.', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


# ── Admin: dashboard ──────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
def admin_dashboard():
    stats = {
        'posts':      Post.query.count(),
        'published':  Post.query.filter_by(published=True).count(),
        'projects':   Project.query.count(),
        'messages':   Message.query.count(),
        'unread':     Message.query.filter_by(read=False).count(),
    }
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()
    recent_posts    = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_messages=recent_messages,
                           recent_posts=recent_posts)


# ── Admin: posts ──────────────────────────────────────────────────────────────

@app.route('/admin/posts')
@login_required
def admin_posts():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('admin/posts.html', posts=posts)


@app.route('/admin/posts/new', methods=['GET', 'POST'])
@login_required
def admin_post_new():
    if request.method == 'POST':
        title     = request.form.get('title', '').strip()
        excerpt   = request.form.get('excerpt', '').strip()
        body      = request.form.get('body', '').strip()
        category  = request.form.get('category', 'General').strip()
        tags      = request.form.get('tags', '').strip()
        published = 'published' in request.form

        if not all([title, excerpt, body]):
            flash('Title, excerpt and body are required.', 'error')
            return render_template('admin/post_form.html', post=None, form=request.form)

        slug = slugify(title)
        # Ensure unique slug
        base, counter = slug, 1
        while Post.query.filter_by(slug=slug).first():
            slug = f'{base}-{counter}'
            counter += 1

        post = Post(title=title, slug=slug, excerpt=excerpt, body=body,
                    category=category, tags=tags, published=published)
        db.session.add(post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('admin_posts'))

    return render_template('admin/post_form.html', post=None, form={})


@app.route('/admin/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_post_edit(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        post.title     = request.form.get('title', '').strip()
        post.excerpt   = request.form.get('excerpt', '').strip()
        post.body      = request.form.get('body', '').strip()
        post.category  = request.form.get('category', 'General').strip()
        post.tags      = request.form.get('tags', '').strip()
        post.published = 'published' in request.form

        if not all([post.title, post.excerpt, post.body]):
            flash('Title, excerpt and body are required.', 'error')
            return render_template('admin/post_form.html', post=post, form=request.form)

        db.session.commit()
        flash('Post updated!', 'success')
        return redirect(url_for('admin_posts'))

    return render_template('admin/post_form.html', post=post, form={})


@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_post_delete(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'info')
    return redirect(url_for('admin_posts'))


# ── Admin: messages ───────────────────────────────────────────────────────────

@app.route('/admin/messages')
@login_required
def admin_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)


@app.route('/admin/messages/<int:msg_id>')
@login_required
def admin_message_view(msg_id):
    msg = Message.query.get_or_404(msg_id)
    if not msg.read:
        msg.read = True
        db.session.commit()
    return render_template('admin/message_view.html', msg=msg)


@app.route('/admin/messages/<int:msg_id>/delete', methods=['POST'])
@login_required
def admin_message_delete(msg_id):
    msg = Message.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'info')
    return redirect(url_for('admin_messages'))


# ── Admin: projects ───────────────────────────────────────────────────────────

@app.route('/admin/projects')
@login_required
def admin_projects():
    projects = Project.query.order_by(Project.order).all()
    return render_template('admin/projects.html', projects=projects)


@app.route('/admin/projects/new', methods=['GET', 'POST'])
@login_required
def admin_project_new():
    if request.method == 'POST':
        project = Project(
            title          = request.form.get('title', '').strip(),
            description    = request.form.get('description', '').strip(),
            tech_stack     = request.form.get('tech_stack', '').strip(),
            category       = request.form.get('category', 'Web').strip(),
            image_url      = request.form.get('image_url', '').strip(),
            live_url       = request.form.get('live_url', '').strip(),
            github_url     = request.form.get('github_url', '').strip(),
            highlights     = request.form.get('highlights', '').strip(),
            icon           = request.form.get('icon', '🚀').strip() or '🚀',
            thumb_color    = request.form.get('thumb_color', 'default').strip() or 'default',
            category_label = request.form.get('category_label', '').strip(),
            featured       = 'featured' in request.form,
            order          = int(request.form.get('order', 0) or 0),
        )
        db.session.add(project)
        db.session.commit()
        flash('Project added!', 'success')
        return redirect(url_for('admin_projects'))

    return render_template('admin/project_form.html', project=None, form={})


@app.route('/admin/projects/<int:proj_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_project_edit(proj_id):
    project = Project.query.get_or_404(proj_id)

    if request.method == 'POST':
        project.title          = request.form.get('title', '').strip()
        project.description    = request.form.get('description', '').strip()
        project.tech_stack     = request.form.get('tech_stack', '').strip()
        project.category       = request.form.get('category', 'Web').strip()
        project.image_url      = request.form.get('image_url', '').strip()
        project.live_url       = request.form.get('live_url', '').strip()
        project.github_url     = request.form.get('github_url', '').strip()
        project.highlights     = request.form.get('highlights', '').strip()
        project.icon           = request.form.get('icon', '🚀').strip() or '🚀'
        project.thumb_color    = request.form.get('thumb_color', 'default').strip() or 'default'
        project.category_label = request.form.get('category_label', '').strip()
        project.featured       = 'featured' in request.form
        project.order          = int(request.form.get('order', 0) or 0)
        db.session.commit()
        flash('Project updated!', 'success')
        return redirect(url_for('admin_projects'))

    return render_template('admin/project_form.html', project=project, form={})


@app.route('/admin/projects/<int:proj_id>/delete', methods=['POST'])
@login_required
def admin_project_delete(proj_id):
    project = Project.query.get_or_404(proj_id)
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'info')
    return redirect(url_for('admin_projects'))


# ── CLI: init db + create admin ───────────────────────────────────────────────

@app.cli.command('init-db')
def init_db():
    """Create all tables."""
    db.create_all()
    print('Database tables created.')


@app.cli.command('migrate-projects')
def migrate_projects():
    """Add the highlights/icon/thumb_color/category_label columns to existing projects table."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    existing = {col['name'] for col in inspector.get_columns('projects')}

    plan = []
    if 'highlights' not in existing:
        plan.append(('highlights',     "ALTER TABLE projects ADD COLUMN highlights TEXT DEFAULT ''"))
    if 'icon' not in existing:
        plan.append(('icon',           "ALTER TABLE projects ADD COLUMN icon VARCHAR(16) DEFAULT ''"))
    if 'thumb_color' not in existing:
        plan.append(('thumb_color',    "ALTER TABLE projects ADD COLUMN thumb_color VARCHAR(40) DEFAULT 'default'"))
    if 'category_label' not in existing:
        plan.append(('category_label', "ALTER TABLE projects ADD COLUMN category_label VARCHAR(80) DEFAULT ''"))

    if not plan:
        print('Projects table already up to date.')
        return

    with db.engine.begin() as conn:
        for col, stmt in plan:
            conn.execute(text(stmt))
            print(f'  [OK] added column: {col}')
    print(f'Applied {len(plan)} migration(s).')


@app.cli.command('seed-projects')
def seed_projects():
    """Insert the 5 portfolio showcase projects (idempotent — skips by title)."""
    seeds = [
        {
            'title':       'AllNewUsed',
            'description': "Ghana's #1 marketplace for importing vehicles and parts. A full-featured "
                           "classifieds platform serving buyers and sellers in Accra, Kumasi, Tamale "
                           "and Takoradi, with over 3,000 active listings and verified dealer profiles.",
            'tech_stack':  'Python, Flask, SQLite, HTML/CSS/JS',
            'category':    'Web',
            'category_label': 'Web · Marketplace',
            'live_url':    'https://allnewused.com',
            'icon':        '🚗',
            'thumb_color': 'marketplace',
            'highlights':  'Vehicle listings with filters\n'
                           'Verified dealer accounts\n'
                           'Multi-city coverage (4 cities)\n'
                           'User auth & registration\n'
                           'Image upload for listings\n'
                           '3,257+ active listings',
            'featured':    True,
            'order':       1,
        },
        {
            'title':       'BigBrands+',
            'description': 'A jobs and business advertising platform for Ghana. Users can discover '
                           'verified job listings and business ads all in one place, with free '
                           'applications and a clean, easy-to-use interface.',
            'tech_stack':  'Python, Flask, SQLite, HTML/CSS/JS',
            'category':    'Web',
            'category_label': 'Web · Jobs & Ads',
            'live_url':    'https://bigbrandsplus.com',
            'icon':        '💼',
            'thumb_color': 'jobs',
            'highlights':  '72+ active job listings\n'
                           'Business ad management\n'
                           'Free to apply for candidates\n'
                           'User auth & profiles\n'
                           'Admin moderation panel\n'
                           'Responsive mobile design',
            'featured':    True,
            'order':       2,
        },
        {
            'title':       'Alaafie Medical Centre',
            'description': 'A professional website for a medical centre in Ghana. Clean, trustworthy '
                           'design communicating services, doctors, and contact information — helping '
                           'patients find and book the care they need quickly.',
            'tech_stack':  'Python, Flask, HTML/CSS/JS',
            'category':    'Web',
            'category_label': 'Web · Healthcare',
            'live_url':    'https://alaafiemedicalcentre.com',
            'icon':        '🏥',
            'thumb_color': 'medical',
            'highlights':  'Services & departments pages\n'
                           'Doctors / team profiles\n'
                           'Appointment contact form\n'
                           'Mobile-first responsive layout\n'
                           'Location & hours info\n'
                           'SEO optimised',
            'featured':    False,
            'order':       3,
        },
        {
            'title':       'MadeInGH',
            'description': 'An e-commerce platform celebrating and selling proudly Ghanaian-made '
                           'products. Showcasing local brands, artisans and manufacturers — connecting '
                           'Ghanaian makers with buyers locally and internationally.',
            'tech_stack':  'Python, Flask, SQLite, HTML/CSS/JS',
            'category':    'Web',
            'category_label': 'Web · E-commerce',
            'live_url':    'https://madeingh.com',
            'icon':        '🇬🇭',
            'thumb_color': 'ecommerce',
            'highlights':  'Product listings & categories\n'
                           'Vendor / seller profiles\n'
                           'Shopping cart & checkout\n'
                           'Mobile money integration\n'
                           '"Made in Ghana" brand focus\n'
                           'Admin product management',
            'featured':    False,
            'order':       4,
        },
        {
            'title':       'Crown & Counsel Law Firm',
            'description': 'A professional, authoritative website for a law firm. Designed to project '
                           'trust and credibility, showcasing practice areas, attorney profiles, '
                           'and making it easy for clients to get in touch.',
            'tech_stack':  'Python, Flask, HTML/CSS/JS',
            'category':    'Web',
            'category_label': 'Web · Legal',
            'live_url':    'https://crownandcounsellawfirm.com',
            'icon':        '⚖️',
            'thumb_color': 'law',
            'highlights':  'Practice areas pages\n'
                           'Attorney / team profiles\n'
                           'Client consultation form\n'
                           'Professional brand design\n'
                           'SEO optimised\n'
                           'Fast, secure hosting setup',
            'featured':    False,
            'order':       5,
        },
    ]

    inserted, skipped = 0, 0
    for data in seeds:
        if Project.query.filter_by(title=data['title']).first():
            print(f'  [SKIP] "{data["title"]}" already exists.')
            skipped += 1
            continue
        db.session.add(Project(**data))
        inserted += 1
        print(f'  [ADD] "{data["title"]}".')

    db.session.commit()
    print(f'Done. Inserted {inserted}, skipped {skipped}.')


@app.cli.command('create-admin')
def create_admin():
    """Create the admin user (run once)."""
    import getpass
    username = input('Admin username: ').strip()
    password = getpass.getpass('Admin password: ')

    if Admin.query.filter_by(username=username).first():
        print(f'User "{username}" already exists.')
        return

    admin = Admin(username=username)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f'Admin "{username}" created successfully.')


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
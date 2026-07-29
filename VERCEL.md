# Deploying to Vercel

This app runs on Vercel as a single Python serverless function. `api/index.py`
imports the Flask app from the repo root; `vercel.json` routes `/static/*` to
Vercel's CDN and everything else to the function.

**The one hard requirement:** Vercel gives serverless functions a *read-only*
filesystem, so the SQLite file cannot be used in production. The admin CMS, the
blog, and the contact form all write to the database, so you need hosted
Postgres. The steps below use Neon.

---

## 1. Push the repo to GitHub

```bash
git add .
git commit -m "Add Vercel deployment config"
git push Emjudecodingtech main
```

## 2. Import the project and set the environment variables

The database can only be attached *after* the project exists, so the order is
import → deploy → attach Neon → redeploy. The first deploy will fail at
runtime; that is expected and step 3 fixes it.

1. Go to <https://vercel.com/new> and sign in with GitHub.
2. Import `kingkong-nyame/emjudecodingtech`.
3. Leave every build setting at its default — `vercel.json` overrides the
   auto-detected Flask preset anyway.
4. Expand **Environment Variables** and click **Import .env**, selecting your
   local `.env`. It must contain:

   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | A long random string — generate with `python -c "import secrets; print(secrets.token_hex(32))"` |
   | `MAIL_SERVER` | `smtp.gmail.com` |
   | `MAIL_PORT` | `465` |
   | `MAIL_USERNAME` | Your Gmail address |
   | `MAIL_PASSWORD` | A 16-character [Gmail App Password](https://myaccount.google.com/apppasswords), spaces removed — not your account password |
   | `CONTACT_RECEIVER` | Where enquiries should land |

   Two traps here. `SECRET_KEY` is not optional: without it the app falls back
   to a hard-coded development value that is visible in this public repo, and
   anyone could forge an admin session cookie. And do **not** put `DATABASE_URL`
   in the imported `.env` — Neon supplies that in the next step, and a manually
   set value would collide with it.

5. Click **Deploy**. The build should succeed but the site will return 500s,
   because there is no database yet.

## 3. Attach the Neon database

1. In the project dashboard, open the **Storage** tab.
2. **Create Database → Neon → Postgres**, pick a region near your users
   (Frankfurt `eu-central-1` is a good default for West Africa), create it.
3. Make sure it is connected to this project.

Vercel injects `DATABASE_URL` into the project automatically — you do not need
to copy it anywhere. Neon hands out a *pooled* connection string
(`...-pooler...`), which is what a serverless app should use.

## 4. Redeploy

**Deployments →** latest deployment **→ ⋯ → Redeploy.** A running deployment
does not pick up new environment variables on its own. From here on, every push
to `main` deploys automatically.

The site will still 500 at this point — the database exists but has no tables.
Step 5 is what brings it up.

## 5. Create the tables and your admin user

The Flask CLI can't run on Vercel, so run it locally against the Neon database —
it's the same database the deployment uses.

Copy the connection string from **Storage → your database → `DATABASE_URL`**, then:

```bash
# PowerShell
$env:DATABASE_URL = "postgresql://...-pooler...neon.tech/...?sslmode=require"
$env:FLASK_APP = "app.py"

pip install -r requirements.txt   # psycopg2-binary is needed to reach Postgres
flask init-db
flask seed-projects
flask create-admin                # prompts for username + password
```

```bash
# macOS / Linux
export DATABASE_URL="postgresql://...-pooler...neon.tech/...?sslmode=require"
export FLASK_APP=app.py

pip install -r requirements.txt
flask init-db
flask seed-projects
flask create-admin
```

Then visit `https://<your-project>.vercel.app/admin/login`.

> Careful: while `DATABASE_URL` is set in your shell, `flask run` also points at
> production. Open a fresh terminal for local development, or unset the variable.

---

## Things to watch

**Contact-form emails and the function timeout.** The contact route sends two
emails over SMTP before returning a response. On Vercel's Hobby plan a function
is capped at 10 seconds by default, and a Gmail SSL handshake plus two sends can
get close to that on a cold start. The message is written to the database first,
so an enquiry is never lost — but if you see timeouts, switch to an HTTP email
API (Resend, SendGrid, Postmark) instead of SMTP. Those are a single fast HTTPS
call and are the normal choice for serverless.

**Nothing on disk survives.** Anything written to the filesystem at runtime is
discarded when the container is recycled. If you later add image uploads, they
need to go to object storage (Vercel Blob, S3, Cloudinary) rather than `static/`.

**Cold starts.** The first request after an idle period pays for the Python
runtime plus the SQLAlchemy engine warming up — usually a second or two.

**`migrate-projects`.** The existing `flask migrate-projects` command is only
needed for a database created before the `highlights`/`icon`/`thumb_color`/
`category_label` columns existed. A fresh `init-db` already includes them.

---

## Local development is unchanged

With no `DATABASE_URL` set, `config.py` still falls back to
`sqlite:///emjude.db`, so `flask run` works exactly as it did before.

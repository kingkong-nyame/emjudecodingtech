from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = 'kingkongnhyame'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')


@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    name = request.form['name']
    email = request.form['email']
    message = request.form['message']
    # Add your logic here to process the form (e.g., send an email, save to database)
    flash('Thank you for your message! We will get back to you soon.')
    return redirect(url_for('contact'))

if __name__ == '__main__':
    app.run(debug=True)

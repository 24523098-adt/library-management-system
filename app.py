from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SECRET_KEY'] = 'secretkey123'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    available = db.Column(db.Boolean, default=True)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    due_date = db.Column(db.DateTime)
    book = db.relationship('Book', backref='loans')
    user = db.relationship('User', backref='loans')

@app.route('/')
def index():
    books = Book.query.all()
    return render_template('index.html', books=books)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        db.session.add(User(username=username, password=password, role=role))
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard') if user.role == 'pustakawan' else url_for('index'))
        flash('Login gagal')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if session.get('role') != 'pustakawan':
        return redirect(url_for('index'))
    loans = Loan.query.all()
    return render_template('dashboard.html', loans=loans)

@app.route('/search')
def search():
    q = request.args.get('q', '')
    books = Book.query.filter(Book.title.contains(q) | Book.author.contains(q)).all()
    return render_template('index.html', books=books, query=q)

@app.route('/borrow/<int:book_id>')
def borrow(book_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    book = Book.query.get(book_id)
    if book and book.available:
        loan = Loan(book_id=book_id, user_id=session['user_id'], status='pending', due_date=datetime.now()+timedelta(days=7))
        book.available = False
        db.session.add(loan)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/approve/<int:loan_id>')
def approve(loan_id):
    if session.get('role') != 'pustakawan':
        return redirect(url_for('index'))
    loan = Loan.query.get(loan_id)
    loan.status = 'approved'
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/return/<int:loan_id>')
def return_book(loan_id):
    if session.get('role') != 'pustakawan':
        return redirect(url_for('index'))
    loan = Loan.query.get(loan_id)
    loan.status = 'returned'
    loan.book.available = True
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if session.get('role') != 'pustakawan':
        return redirect(url_for('index'))
    if request.method == 'POST':
        db.session.add(Book(title=request.form['title'], author=request.form['author']))
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_book.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
import os
import sqlite3
from flask import Flask, request, redirect, url_for, render_template_string, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# -------------------------
# DATABASE FUNCTIONS
# -------------------------
def get_db():
    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    return conn


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    cur.connection.commit()
    cur.close()
    return (rv[0] if rv else None) if one else rv


# -------------------------
# INIT DATABASE
# -------------------------
def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user'
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            price INTEGER,
            stock INTEGER,
            image TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            book_id INTEGER,
            qty INTEGER,
            fullname TEXT,
            address TEXT,
            city TEXT,
            postal_code TEXT,
            payment_method TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    # admin
    if not query("SELECT * FROM users WHERE email=?", ("admin@store",), one=True):
        db.execute(
            "INSERT INTO users (name,email,password,role) VALUES (?, ?, ?, ?)",
            ("Admin", "admin@store", generate_password_hash("admin", method="pbkdf2:sha256"), "admin")
        )
    db.commit()


# -------------------------
# FILE UPLOAD
# -------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------
# GLOBAL STYLES (твой улучшенный CSS)
# -------------------------
STYLES = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BookStore</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        /* Glass morphism header */
        header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 15px 40px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }

        .nav {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }

        .logo {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-decoration: none;
        }

        .nav-links {
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }

        .nav a, .nav span {
            text-decoration: none;
            color: #555;
            font-weight: 600;
            transition: all 0.3s ease;
            padding: 8px 15px;
            border-radius: 25px;
        }

        .nav a:hover {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            transform: translateY(-2px);
        }

        .user-name {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            border-radius: 25px;
        }

        main {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px;
        }

        /* Modern grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }

        /* Fancy cards */
        .card {
            background: white;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            position: relative;
        }

        .card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }

        .card img {
            width: 100%;
            height: 300px;
            object-fit: cover;
            transition: transform 0.3s;
        }

        .card:hover img {
            transform: scale(1.05);
        }

        .card-body {
            padding: 20px;
            position: relative;
            background: white;
        }

        .card-body b {
            display: block;
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #333;
        }

        .author {
            color: #888;
            font-size: 14px;
            margin: 5px 0;
            display: flex;
            align-items: center;
            gap: 5px;
        }

        .price {
            font-size: 24px;
            font-weight: 800;
            color: #667eea;
            margin: 10px 0;
        }

        .stock {
            display: inline-block;
            background: #e8f5e9;
            color: #2e7d32;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin: 10px 0;
        }

        .btn {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
            border: none;
            cursor: pointer;
            margin-top: 10px;
        }

        .btn:hover {
            transform: translateX(5px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        /* Forms */
        .form-container {
            max-width: 500px;
            margin: 50px auto;
            background: white;
            padding: 40px;
            border-radius: 30px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.1);
        }

        .form-container h2 {
            margin-bottom: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
        }

        .form-group {
            margin-bottom: 20px;
        }

        input, select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            font-size: 16px;
            transition: all 0.3s;
        }

        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        /* Cart styles */
        .cart-item {
            background: white;
            padding: 20px;
            margin: 10px 0;
            border-radius: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }

        .cart-item:hover {
            transform: translateX(10px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .total {
            font-size: 28px;
            font-weight: 800;
            color: #667eea;
            text-align: right;
            margin: 20px 0;
        }

        /* Alerts */
        .alert {
            padding: 15px;
            border-radius: 15px;
            margin-bottom: 20px;
            text-align: center;
        }

        .alert-success {
            background: #d4edda;
            color: #155724;
        }

        /* Responsive */
        @media (max-width: 768px) {
            main {
                padding: 20px;
            }

            .grid {
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
            }

            .nav {
                flex-direction: column;
            }
        }

        /* Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .card {
            animation: fadeInUp 0.6s ease-out;
        }
    </style>
</head>
<body>
"""

FOOTER = """
</body>
</html>
"""


def render_page(content):
    """Helper function to wrap content with styles"""
    return STYLES + content + FOOTER


# -------------------------
# ROUTES
# -------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        pw = request.form["pw"]
        if query("SELECT * FROM users WHERE email=?", (email,), one=True):
            return render_page(
                "<div class='form-container'><div class='alert alert-success'>User already exists</div><a href='/register' class='btn'>Try again</a></div>")
        db = get_db()
        db.execute("INSERT INTO users (name,email,password) VALUES (?, ?, ?)",
                   (name, email, generate_password_hash(pw, method="pbkdf2:sha256")))
        db.commit()
        return redirect("/login")

    content = """
    <div class="form-container">
        <h2>📝 Create Account</h2>
        <form method="post">
            <div class="form-group">
                <input type="text" name="name" placeholder="Full Name" required>
            </div>
            <div class="form-group">
                <input type="email" name="email" placeholder="Email" required>
            </div>
            <div class="form-group">
                <input type="password" name="pw" placeholder="Password" required>
            </div>
            <button type="submit">Register</button>
        </form>
        <p style="text-align: center; margin-top: 20px;">Already have an account? <a href="/login" style="color: #667eea;">Login</a></p>
    </div>
    """
    return render_page(content)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["pw"]
        user = query("SELECT * FROM users WHERE email=?", (email,), one=True)
        if not user or not check_password_hash(user["password"], pw):
            return render_page(
                "<div class='form-container'><div class='alert alert-success'>Wrong email or password</div><a href='/login' class='btn'>Try again</a></div>")
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        session["name"] = user["name"]
        session["cart"] = {}
        return redirect("/")

    content = """
    <div class="form-container">
        <h2>🔐 Welcome Back</h2>
        <form method="post">
            <div class="form-group">
                <input type="email" name="email" placeholder="Email" required>
            </div>
            <div class="form-group">
                <input type="password" name="pw" placeholder="Password" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <p style="text-align: center; margin-top: 20px;">New here? <a href="/register" style="color: #667eea;">Create Account</a></p>
    </div>
    """
    return render_page(content)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/")
def index():
    books = query("SELECT * FROM books")

    # Generate nav HTML
    nav_html = """
    <header>
        <div class="nav">
            <a href="/" class="logo">📚 BookStore</a>
            <div class="nav-links">
    """
    if 'user_id' in session:
        nav_html += f"""
            <span class="user-name">👋 {session['name']}</span>
            <a href="/cart"><i class="fas fa-shopping-cart"></i> Cart</a>
            <a href="/logout"><i class="fas fa-sign-out-alt"></i> Logout</a>
        """
        if session['role'] == 'admin':
            nav_html += f'<a href="/admin"><i class="fas fa-cog"></i> Admin</a>'
    else:
        nav_html += """
            <a href="/login"><i class="fas fa-sign-in-alt"></i> Login</a>
            <a href="/register"><i class="fas fa-user-plus"></i> Register</a>
        """

    nav_html += """
            </div>
        </div>
    </header>
    <main>
        <div class="grid">
    """

    for b in books:
        nav_html += f"""
            <div class="card">
                <img src="{b['image']}" alt="{b['title']}">
                <div class="card-body">
                    <b>{b['title']}</b>
                    <div class="author"><i class="fas fa-user"></i> {b['author']}</div>
                    <div class="price">₸{b['price']:,}</div>
                    <span class="stock"><i class="fas fa-box"></i> {b['stock']} left</span>
                    <br>
                    <a href="/book/{b['id']}" class="btn"><i class="fas fa-eye"></i> View Details</a>
                </div>
            </div>
        """

    nav_html += """
        </div>
    </main>
    """

    return render_page(nav_html)


@app.route("/book/<int:book_id>", methods=["GET", "POST"])
def book_detail(book_id):
    b = query("SELECT * FROM books WHERE id=?", (book_id,), one=True)
    if not b:
        return render_page(
            "<div class='form-container'><h2>Book not found</h2><a href='/' class='btn'>Go Back</a></div>")

    if request.method == "POST":
        qty = int(request.form["qty"])
        cart = session.get("cart", {})
        cart[book_id] = cart.get(book_id, 0) + qty
        session["cart"] = cart
        return redirect("/cart")

    content = f"""
    <main style="max-width: 1000px; margin: 0 auto;">
        <div style="background: white; border-radius: 30px; overflow: hidden; display: grid; grid-template-columns: 1fr 1fr; gap: 30px; padding: 30px;">
            <div>
                <img src="{b['image']}" style="width: 100%; border-radius: 20px;">
            </div>
            <div>
                <h1 style="font-size: 36px; margin-bottom: 10px;">{b['title']}</h1>
                <div class="author" style="font-size: 18px;"><i class="fas fa-user"></i> {b['author']}</div>
                <div class="price" style="font-size: 36px;">₸{b['price']:,}</div>
                <span class="stock"><i class="fas fa-box"></i> {b['stock']} available</span>
                <form method="post" style="margin-top: 30px;">
                    <div class="form-group">
                        <label>Quantity:</label>
                        <input type="number" name="qty" min="1" max="{b['stock']}" value="1" style="width: auto;">
                    </div>
                    <button type="submit" class="btn" style="width: auto;"><i class="fas fa-cart-plus"></i> Add to Cart</button>
                </form>
                <br>
                <a href="/" class="btn" style="background: #6c757d;"><i class="fas fa-arrow-left"></i> Back to Shop</a>
            </div>
        </div>
    </main>
    """
    return render_page(content)


@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    if not cart:
        return render_page(
            "<div class='form-container'><h2>🛒 Your cart is empty</h2><a href='/' class='btn'>Continue Shopping</a></div>")

    items = []
    total = 0
    for book_id, qty in cart.items():
        b = query("SELECT * FROM books WHERE id=?", (book_id,), one=True)
        items.append((b, qty))
        total += b["price"] * qty

    items_html = ""
    for b, qty in items:
        items_html += f"""
        <div class="cart-item">
            <div>
                <b>{b['title']}</b><br>
                <small>{b['author']}</small>
            </div>
            <div>
                {qty} x ₸{b['price']:,} = <b>₸{b['price'] * qty:,}</b>
            </div>
        </div>
        """

    content = f"""
    <main>
        <h1 style="color: white; margin-bottom: 30px;">🛒 Shopping Cart</h1>
        {items_html}
        <div class="total">Total: ₸{total:,}</div>
        <div style="background: white; padding: 30px; border-radius: 30px; margin-top: 30px;">
            <h3>Checkout Information</h3>
            <form method="post" action="/checkout">
                <div class="form-group">
                    <input type="text" name="fullname" placeholder="Full Name" required>
                </div>
                <div class="form-group">
                    <input type="text" name="address" placeholder="Address" required>
                </div>
                <div class="form-group">
                    <input type="text" name="city" placeholder="City" required>
                </div>
                <div class="form-group">
                    <input type="text" name="postal_code" placeholder="Postal Code" required>
                </div>
                <div class="form-group">
                    <select name="payment_method">
                        <option>Cash on delivery</option>
                        <option>Card online</option>
                    </select>
                </div>
                <button type="submit"><i class="fas fa-check-circle"></i> Confirm Order</button>
            </form>
        </div>
        <br>
        <a href="/" class="btn"><i class="fas fa-arrow-left"></i> Continue Shopping</a>
    </main>
    """
    return render_page(content)


@app.route("/checkout", methods=["POST"])
def checkout():
    if "user_id" not in session:
        return redirect("/login")
    cart = session.get("cart", {})
    user_id = session["user_id"]
    fullname = request.form["fullname"]
    address = request.form["address"]
    city = request.form["city"]
    postal_code = request.form["postal_code"]
    payment_method = request.form["payment_method"]

    for book_id, qty in cart.items():
        query("""INSERT INTO orders 
                 (user_id, book_id, qty, fullname, address, city, postal_code, payment_method)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (user_id, book_id, qty, fullname, address, city, postal_code, payment_method))
        query("UPDATE books SET stock=stock-? WHERE id=?", (qty, book_id))
    session["cart"] = {}

    return render_page("""
    <div class="form-container" style="text-align: center;">
        <i class="fas fa-check-circle" style="font-size: 80px; color: #28a745;"></i>
        <h2>Order Completed! 🎉</h2>
        <p>Thank you for your purchase!</p>
        <a href="/" class="btn">Continue Shopping</a>
    </div>
    """)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "role" not in session or session["role"] != "admin":
        return render_page(
            "<div class='form-container'><h2>Access Denied</h2><a href='/' class='btn'>Go Back</a></div>")

    if request.method == "POST":
        file = request.files.get("image")
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            image_path = "/" + path.replace("\\", "/")
        else:
            image_path = "/static/uploads/no_image.png"
        query("INSERT INTO books (title,author,price,stock,image) VALUES (?, ?, ?, ?, ?)",
              (request.form["title"], request.form["author"], int(request.form["price"]),
               int(request.form["stock"]), image_path))
        return redirect("/admin")

    books = query("SELECT * FROM books")

    books_html = ""
    for b in books:
        books_html += f"""
        <div style="background: white; padding: 15px; border-radius: 15px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <b>{b['title']}</b> — ₸{b['price']:,} — Stock: {b['stock']}
            </div>
            <form method="post" action="/delete_book/{b['id']}" style="margin: 0;">
                <button type="submit" style="background: #dc3545; width: auto;"><i class="fas fa-trash"></i> Delete</button>
            </form>
        </div>
        """

    content = f"""
    <main>
        <h1 style="color: white;">⚙️ Admin Panel</h1>
        <div style="background: white; padding: 30px; border-radius: 30px; margin-bottom: 30px;">
            <h2>Add New Book</h2>
            <form method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <input name="title" placeholder="Title" required>
                </div>
                <div class="form-group">
                    <input name="author" placeholder="Author" required>
                </div>
                <div class="form-group">
                    <input type="number" name="price" placeholder="Price" required>
                </div>
                <div class="form-group">
                    <input type="number" name="stock" placeholder="Stock" required>
                </div>
                <div class="form-group">
                    <input type="file" name="image" accept="image/*">
                </div>
                <button type="submit"><i class="fas fa-plus"></i> Add Book</button>
            </form>
        </div>

        <h2 style="color: white;">Manage Books</h2>
        {books_html}

        <br>
        <a href="/" class="btn"><i class="fas fa-arrow-left"></i> Back to Shop</a>
    </main>
    """
    return render_page(content)


@app.route("/delete_book/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    if "role" not in session or session["role"] != "admin":
        return render_page("<div class='form-container'><h2>Access Denied</h2></div>")
    book = query("SELECT * FROM books WHERE id=?", (book_id,), one=True)
    if book and book["image"] and os.path.exists(book["image"].lstrip("/")):
        try:
            os.remove(book["image"].lstrip("/"))
        except:
            pass
    query("DELETE FROM books WHERE id=?", (book_id,))
    return redirect("/admin")


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

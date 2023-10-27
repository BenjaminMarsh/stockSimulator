import os

from time import sleep
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    portfolio = []
    totalvalue = 0
    total = 0
    money = db.execute("Select cash from users where id = :id", id = session["user_id"])
    stocklist = db.execute("SELECT Distinct symbol from transactions WHERE user_id = :id", id = session["user_id"])
    cash = money[0]['cash']
    for item in stocklist:
        symbol = item["symbol"]
        sharelist = db.execute("SELECT SUM(shares) from transactions where user_id = :id AND symbol = :symbol", symbol = symbol, id = session["user_id"])
        shares = sharelist[0]["SUM(shares)"]
        look= lookup(symbol)
        stockdict = {
            
            "symbol": symbol,
            "pps": look['price'],
            "shares": shares,
            "value": look['price']*shares,
            "company": look['name'],

        }
        total += look['price']* shares
        totalvalue = total + cash
        portfolio.append(stockdict)
        
        
    return render_template("index.html", portfolio = portfolio, cash = cash, total = total, totalvalue = totalvalue)
    

    return apology("TODO")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = request.form.get("symbol")
        shares= int(request.form.get("shares"))
        print(f"{shares} of {symbol}")
        if shares < 1:
            flash("You must buy at least one share")
            return render_template("buy.html")
        look = lookup(symbol)
        price = look['price']
        result = db.execute("SELECT cash from users WHERE id = :id", id = session["user_id"])
        cash = result[0]["cash"]
        if price * shares > cash:
            flash("You don't have the money")
            return render_template("buy.html")
        db.execute("UPDATE users SET cash = cash - :cost WHERE id = :id", cost = price * shares, id = session["user_id"])
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) values (:user_id, :symbol, :shares, :price)", user_id = session["user_id"], symbol = symbol, shares = shares, price = price)
        flash("You bought stock!")
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    transactions = db.execute("SELECT * from transactions where user_id = :id", id = session["user_id"])
    return render_template("history.html", transactions = transactions)
        
        
        
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)


        # Remember which user has logged in
        else:
            session["user_id"] = rows[0]["id"]

        # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/addmon", methods=["GET", "POST"])
@login_required
def addmon():
    if request.method == "GET":
        return render_template("addmon.html")
    else:
        invest = request.form.get("invest")
        withdraw = request.form.get("withdraw")
        print(f"{withdraw}{invest}")
        if withdraw == "":
            db.execute("UPDATE users SET cash = cash + :invest WHERE id = :id", invest = invest, id = session["user_id"])
            flash("Congratulations on investing for the future!")
            return redirect("/")
        elif invest == "":
            db.execute("UPDATE users SET cash = cash - :withdraw WHERE id = :id", withdraw = withdraw, id = session["user_id"])
            flash("Congratulations on knowing when to walk away!")
            return redirect("/")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
        return render_template("quote.html")
    else:
        quote = request.form.get("quote")
        look = lookup(quote)
        quoteprice = look['price']
        quotename = look['name']
        return render_template("quoted.html", quoteprice = quoteprice, quotename = quotename)


@app.route("/register", methods=["GET", "POST"])
def register():
    print("0")

    print("1")

    if request.method == "POST":
        username = request.form.get("usernameset")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        if (password1 == password2):
            print("2")
            password = password1
            usercheck=db.execute("SELECT * FROM users WHERE username LIKE :username", username=username)
            if len(usercheck) != 0:
                print("3")
                return render_template("register.html")
            else:

                db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)", username=username, password=generate_password_hash(password))
                rows = db.execute("SELECT * FROM users WHERE username = :username",username=username)
                session["user_id"] = rows[0]["id"]
                return redirect("/")
        else:
            flash("Those passwords do not match")
            return render_template("register.html")
            print("4")
        """Register user"""
        return apology("TODO")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        return render_template("sell.html")
    else:
        sellsymbol = request.form.get("sellsymbol")
        sellshares= int(request.form.get("sellshares"))
        sharelist = db.execute("SELECT SUM(shares) FROM transactions WHERE user_id = :id and symbol = :symbol", id = session["user_id"], symbol = sellsymbol)
        owned_shares = sharelist[0]["SUM(shares)"]
        print(f"{sellsymbol}{sellshares}{owned_shares}{sharelist}")
        if sellshares < 1:
            flash("You must sell at least one share")
            return render_template("sell.html")
        elif sellshares > owned_shares:
            flash("You do not have enough shares")
            return render_template("sell.html")
        look = lookup(sellsymbol)
        price = look['price']
        result = db.execute("SELECT cash from users WHERE id = :id", id = session["user_id"])
        cash = result[0]["cash"]
        db.execute("UPDATE users SET cash = cash + :cost WHERE id = :id", cost = price * sellshares, id = session["user_id"])
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price) values (:user_id, :sellsymbol, :sellshares, :price)", user_id = session["user_id"], sellsymbol = sellsymbol, sellshares = -sellshares, price = price)
        flash("You sold stock!")
        return render_template("sell.html")
        
    """Sell shares of stock"""
    return apology("TODO")

        


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

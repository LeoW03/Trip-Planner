import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from time import gmtime, strftime

from helpers import login_required

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

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Shows lists user has created"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Remembers which list was opened
        session['list_id'] = request.form.get('list_id')

        # Takes user to items
        return redirect("/items")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        

        # Gets user's lists
        lists = db.execute("SELECT * FROM lists WHERE user_id = :user_id",
                              user_id=session["user_id"])

        # Gets username
        username = db.execute("SELECT username FROM users WHERE id=:user_id",
                              user_id=session["user_id"])[0]['username']

        # Renders lists
        return render_template("lists.html", lists=lists, username=username)



@app.route("/items", methods=["GET", "POST"])
@login_required
def items():
    """Shows user's items in a list"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # If user is adding item
        if request.form.get("item") != None:

            # Stores items into database
            db.execute("INSERT INTO items (list_id, item, notes) VALUES(:list_id, :item, :notes)",
                              list_id=session['list_id'], item=request.form.get('item'), notes=request.form.get('notes'))

            # Takes user back to lists
            flash("Added Item","success")
            return redirect("/items")

    # User reached route via GET (as by clicking a link or via redirect)
    else:

        items = db.execute("SELECT * FROM items WHERE list_id=:list_id",
                          list_id=session['list_id'])

        lists = db.execute("SELECT * FROM lists WHERE id=:list_id",
                          list_id=session['list_id'])

        name = lists[0]['name']

        # Renders Template
        return render_template("items.html", items=items, name=name)



@app.route("/deletelist/<int:list_id>", methods=[ "POST"])
@login_required
def deletelist(list_id):
    """Allows user to delete lists"""

    db.execute("DELETE FROM lists WHERE id=:list_id",
                      list_id=list_id)

    # Renders lists
    flash("Deleted List","success")
    return redirect("/")


@app.route("/deleteitem/<int:item_id>", methods=[ "POST"])
@login_required
def deleteitem(item_id):
    """Allows user to delete items from list"""

    db.execute("DELETE FROM items WHERE list_id=:list_id AND id=:id",
                      list_id=session['list_id'], id=item_id)

    items = db.execute("SELECT * FROM items WHERE list_id=:list_id",
                          list_id=session['list_id'])

    lists = db.execute("SELECT * FROM lists WHERE id=:list_id",
                          list_id=session['list_id'])

    name = lists[0]['name']

    flash("Deleted Item","success")
    return redirect("/items")












@app.route("/pack/<int:item_id>", methods=[ "POST"])
@login_required
def pack(item_id):
    """Allows user to check items as 'packed'"""

    items = db.execute("SELECT * FROM items WHERE list_id=:list_id",
                          list_id=session['list_id'])

    item = None
    for x in items:
        if x['id'] == item_id:
            item = x

    if item['packed'] == "FALSE":
        db.execute("UPDATE items SET packed='TRUE' WHERE list_id=:list_id AND id=:id",
                          list_id=session['list_id'], id=item_id)

    else:
        db.execute("UPDATE items SET packed='FALSE' WHERE list_id=:list_id AND id=:id",
                          list_id=session['list_id'], id=item_id)

    return redirect("/items")












@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Allows user to create new trips"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Stores list data in database
        db.execute("INSERT INTO lists (colour, name, user_id) VALUES(:colour, :name, :user_id)",
                          colour=request.form.get("colour"), name=request.form.get("name"), user_id=session["user_id"])

        # Takes user back to lists
        flash("Created List","success")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add.html")












@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must Provide Username","danger")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must Provide Password","danger")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid Password and/or Username","danger")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")





@app.route("/logout")
def logout():
    """Logs user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")







@app.route("/register", methods=["GET", "POST"])
def register():

     # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must Provide Username","danger")
            return render_template("register.html")

        # Ensure username does not already exist
        names = db.execute("SELECT username FROM users")
        for name in names:
            if request.form.get("username") == name['username']:
                flash("Username Taken","danger")
                return render_template("register.html")

        # Ensure password was submitted
        if not request.form.get("password"):
            flash("Must Provide Password","danger")
            return render_template("register.html")

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirm password"):
            flash("Passwords Must Match","danger")
            return render_template("register.html")

        # Stores username and password
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)",
            request.form.get("username"), generate_password_hash(request.form.get("password")))

        # Sends user to login page
        flash("Registered","success")
        return render_template("login.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


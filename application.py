import os

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


#CONFIGURE FLASK
#export FLASK_APP=application.py
#export FLASK_DEBUG=1
#export DATABASE_URL="postgres://svqtoyhlebkhmb:09eb106b051a0c84f4e4e1035f3176093e325a5ae924bc7b889fa30fed88146b@ec2-52-0-155-79.compute-1.amazonaws.com:5432/d5621ijdp3h140"

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route("/")
def index():
	#log in
	if session["user"]:
		return render_template("index.html", username = session["user"])
	else:
		return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
	#log in
	session.clear()
	if request.method == "POST":
		#log user in.
		username = request.form.get("username")
		if not username:
			return "please enter a username"
		password = request.form.get("password")
		if not password:
			return "please enter a password"
		rows = db.execute("SELECT * FROM users WHERE user_id = :username AND hash = :hash", {"username": username, "hash": hash(password)}).fetchall()
		if len(rows) != 1:
			return "Username or password incorrect"
		#store logged-in user in sessions
		session["user"] = username
		session["user_id"] = rows[0]
		return redirect("/")
	else:
		return render_template("login.html")
		
@app.route("/register", methods=["GET", "POST"])
def register():
	#log in
	if request.method == "POST":
		#Register User
		username = request.form.get("username")
		if not username:
			return "did not provide a username"
		password = request.form.get("password")
		if not password:
			return "did not provide password"
		password2 = request.form.get("password2")
		if not password2:
			return "did not provide password confirmation"
		if password != password2:
			return "password mismatch"
		#check if user does not exist
		rows = db.execute("SELECT * FROM users WHERE user_id = :username", {"username": username}).fetchall()
		if rows:
		 	return "Username already taken"
		#insert user into users table
		db.execute("INSERT INTO users (user_id, hash) VALUES (:username, :hash)", {"username": username, "hash": hash(password)})
		db.commit()
		session["user"] = username
		return redirect("/")
	else:
		return render_template("register.html")

@app.route("/logout")
def logout():
	session.clear()
	return redirect("/")
	

# @app.route("/json")
# def json():
# 	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "qy4xEYfpXzoFkifV1zn3Tg", "isbns": "9781632168146"})
# 	print(res.json())
# 	return "all done"


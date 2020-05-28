import os
import requests

from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import hashword

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


#CONFIGURE FLASK
#export FLASK_APP=application.py
#export FLASK_DEBUG=1
#export DATABASE_URL="postgres://gwwwcblhdczxol:67b0d4d765d6cf79bb87facf7af6d0b570dc2d4fa774627f87a6a615e7d542a1@ec2-18-233-32-61.compute-1.amazonaws.com:5432/d6rc68lbapddqb"
# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

#set up log in info

@app.route("/")
def index():
	#log in
	if "user" not in session:
		return render_template("login.html")
	else:
		return render_template("index.html", username = session["user"])

@app.route("/login", methods=["GET", "POST"])
def login():
	#log in
	session.clear()
	if request.method == "POST":
		#log user in.
		username = request.form.get("username").lower()
		if not username:
			return "please enter a username"
		password = request.form.get("password")
		if not password:
			return "please enter a password"
		rows = db.execute("SELECT * FROM users WHERE user_id = :username AND hash = :hash", {"username": username, "hash": hashword(password)}).fetchall()
		if len(rows) != 1:
		  	return "Username or password incorrect"
		 #store logged-in user in sessions
		session["user"] = username
		session["user_id"] = rows
		return render_template("index.html", username = session["user"])
	else:
		return render_template("login.html")
		
@app.route("/register", methods=["GET", "POST"])
def register():
	#log in
	if request.method == "POST":
		#Register User
		username = request.form.get("username").lower()
		if not username:
			return render_template("error.html", message="did not provide a username")
		password = request.form.get("password")
		if not password:
			return render_template("error.html", message="did not provide password")
		password2 = request.form.get("password2")
		if not password2:
			return render_template("error.html", message="did not provide password confirmation")
		if password != password2:
			return render_template("error.html", message="password mismatch")
		#check if user does not exist
		rows = db.execute("SELECT * FROM users WHERE user_id = :username", {"username": username}).fetchall()
		if rows:
		 	return render_template("error.html", message="Username already taken")
		#insert user into users table
		db.execute("INSERT INTO users (user_id, hash) VALUES (:username, :hash)", {"username": username, "hash": hashword(password)})
		db.commit()
		session["user"] = username
		return redirect("/")
	else:
		return render_template("register.html")

@app.route("/logout")
def logout():
	session.clear()
	return redirect("/")

@app.route("/search", methods = ["GET", "POST"])
def search():
	if session.get("user") is None:
		return render_template("login.html")
	if request.method == "POST":
		entry = request.form.get("search")
		if not entry:
			return "enter a search term"
		#perform database query with entry
		results= db.execute("SELECT isbn, author, title, year FROM books WHERE isbn LIKE :entry OR author LIKE :entry OR title LIKE :entry", {"entry": '%' +entry+ '%'}).fetchall()
		return render_template("results.html", results=results)
	else:
		return render_template("index.html")
	#return database results to "/"

@app.route("/review/<string:isbn>", methods=["POST"])
def review(isbn):
	if session.get("user") is None:
		return render_template("login.html")
	#if request.method == "POST":
# 	#submit review for books from 1 - 5
# 	#write opinion
	comment = request.form.get("review")
	rating = int(request.form.get("rating"))
	isbn = isbn
# 	#do not submit multiple reviews for same book
	#insert review, rating, isbn, into reviews table at user_id
	db.execute("INSERT INTO reviews (user_id, isbn, rating, comment) VALUES (:user_id, :isbn, :rating, :comment)", {"user_id": session["user"] ,"isbn": isbn, "rating": rating, "comment": comment})
	db.commit()
#try:
#	flight = int(request.form.get("name"))
#except ValueError:
	return render_template("success.html", message= "review posted successfully!")
	
	#else:
		#return render_template("error.html", message="POSTS REQUESTS ONLY!")
@app.route("/title/<string:info>")
def title(info):
# 	#book page
	if session.get("user") is None:
		return render_template("login.html")
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": info}).fetchone()
	if book is None:
		return render_template("error.html", message="book not found")
	comment = db.execute("SELECT rating, comment FROM reviews WHERE isbn = :isbn AND user_id = :user_id", {"isbn": info, "user_id": session["user"]}).fetchone()
	if comment == None:
		display = 'block'
		shows = 'none'
	else:
		display = 'None'
		shows = 'inline'
	
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "qy4xEYfpXzoFkifV1zn3Tg", "isbns": info})
	if res.status_code != 200:
		raise Exception("API Request Unsuccessful.")
	res = res.json()
	rating = res["books"][0]["work_ratings_count"]
	avg = res["books"][0]["average_rating"]
	

	return render_template("info.html", book = book, comment = comment, display = display, shows=shows, rating = rating, avg =avg)

@app.route("/user")
def user():

	return render_template("")	
@app.route("/api/<string:isbn>")
def book_api(isbn):
	rows = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
	if rows is None:
		return render_template("error.html", message="book not available")
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "qy4xEYfpXzoFkifV1zn3Tg", "isbns": isbn})
	if res.status_code != 200:
		raise Exception("API Request Unsuccessful.")
	res = res.json()
	rating = res["books"][0]["work_ratings_count"]
	avg = res["books"][0]["average_rating"]

	return jsonify({
		"title": rows.title,
    	"author": rows.author,
    	"year": rows.year,
    	"isbn": rows.isbn,
    	"review_count": rating,
    	"average_score": avg
		})
	
	""" res = requests.get("api_link")
	if res.status_code != 200:
		raise Exception("ERROR")
	data = res.json() """

# 	#from search result, when user clicks, this page should give info about particular book.
# 	#display good reads review data, e.g average rating, no. of rating

# @app.route("/api/<string:isbn>")
# def api(isbn):
# 	#method get
# 	#if isbn not exist, return 404
# 	#return JSON response containing book title, author, publication date, isbn no, review count, average score.
# 	{
#     "title": "Memory",
#     "author": "Doug Lloyd",
#     "year": 2015,
#     "isbn": "1632168146",
#     "review_count": 28,
#     "average_score": 5.0
# 	}

# @app.route("/json")
# def json():
# 	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "qy4xEYfpXzoFkifV1zn3Tg", "isbns": "9781632168146"})
# 	print(res.json())
# 	return "all done"


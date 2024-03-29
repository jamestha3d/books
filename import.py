import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
	f = open("books.csv")
	db.execute("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY autoincrement, isbn VARCHAR, title VARCHAR, author VARCHAR, year INTEGER")
	reader = csv.reader(f)
	for isbn, title, author, year in reader:
		db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
		print(f"added book{title} with ISBN:{isbn} by {author} in {year}")
	db.commit()

if __name__ == "__main__":
	main()
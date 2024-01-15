from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()
# API info
MOVIE_SEARCH = "https://api.themoviedb.org/3/search/movie?include_adult=false&language=en-US&page=1"
MOVIE_INFO = "https://api.themoviedb.org/3/movie/"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/original/"
MOVIE_API_KEY = os.getenv("TMDB_API_KEY")  # need an APY key from https://www.themoviedb.org

# Class to Create edit form with
class MyUpdateForm(FlaskForm):
    rating = FloatField(label="Your Rating Out of 10 e.g. 5.5")
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")

class MovieForm(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

# Database
class Base(DeclarativeBase):
    pass

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///my-top-movies.db"
# Extension
db = SQLAlchemy(model_class=Base)
# Initialize the app with the extension
db.init_app(app)
# Define Model/Table
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[str] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

# Create the table schema in the database, Requires application context
# with app.app_context():
#     db.create_all()
# Create a Record
# with app.app_context():
#     new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg")
#     db.session.add(new_movie)
#     db.session.commit()
# with app.app_context():
#     second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg")
#     db.session.add(second_movie)
#     db.session.commit()

@app.route("/")
def home():
    with app.app_context():
        result = db.session.execute(db.select(Movie).order_by(Movie.rating))
        all_movies = result.scalars().all()  # Convert scalarResult to Python List
        for i in range(len(all_movies)):
            all_movies[i].ranking = len(all_movies) - i  # This code sets ranking on decending order
        db.session.commit()    
        return render_template("index.html", movies=all_movies)

@app.route("/edit", methods=["GET", "POST"])
def edit():
    update_form = MyUpdateForm()
    id = request.args.get("id")
    movie_to_update = db.get_or_404(Movie, id)
    if update_form.validate_on_submit():
        movie_to_update.rating = float(update_form.rating.data)
        movie_to_update.review = update_form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", movie=movie_to_update, form=update_form)

@app.route("/delete<int:id>", methods=["GET", "POST"])
def delete(id):
    with app.app_context():
        movie_to_delete = db.get_or_404(Movie, id)
        db.session.delete(movie_to_delete)
        db.session.commit()
        return redirect(url_for("home"))
    
@app.route("/add", methods=["GET", "POST"])
def add():
    form = MovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(MOVIE_SEARCH, params={"api_key": MOVIE_API_KEY, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)

@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    if movie_id:
        movie_api_url = f"{MOVIE_INFO}/{movie_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title = data["title"],
            year = data["release_date"].split("-")[0],  # We split the release date to grab the year only.
            description = data["overview"],
            rating = 0.0,
            ranking = 0,
            review = "None",
            img_url = f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}"
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))
    
if __name__ == '__main__':
    app.run(debug=True)

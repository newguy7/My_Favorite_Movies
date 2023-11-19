from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired
import requests
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.config['SECRET_KEY'] = '9APkEfBA6O6donzWlSihBXox7C0sKR9a'
Bootstrap5(app)

# Create a New Database
db = SQLAlchemy()

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///my-movie-library.db"

# initialize the app with the extension
db.init_app(app)

tmdb_url = "https://api.themoviedb.org/3/search/movie"
tmdb_detail_url = "https://api.themoviedb.org/3/movie"
API_KEY = os.environ.get('TMDB_API_KEY')

all_movies = []

# Create New Table
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

class RateMovieForm(FlaskForm):
    rating = StringField('Your Rating out of 10 e.g. 7.2', validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])    
    submit = SubmitField("Done")

class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])    
    submit = SubmitField("Add Movie")

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars().all() # convert ScalarResult to Python List    

# ------ update the movie.ranking in database -------
    rank = 1
    for movie in all_movies:
        movie.ranking = rank
        rank += 1
        db.session.commit()

    return render_template("index.html", movies=all_movies)

@app.route("/add", methods=["GET", "POST"])
def add():
    add_movie_form = AddMovieForm()
    if request.method == 'POST':
        if add_movie_form.validate_on_submit():
            title = add_movie_form.title.data
            parameter = {
                'query': title,
                'api_key' : API_KEY
            }
            response = requests.get(url=tmdb_url, params=parameter)
            details = response.json()
            #print(details)
            movie_details = details['results']        
            return render_template("select.html", form=add_movie_form,movie_details=movie_details ) 
        return redirect(url_for('home'))
    return render_template("add.html", form=add_movie_form)    
    

@app.route("/update",methods=["GET", "POST"] )
def edit_rating():
    id = request.args.get('id')    
    rate_movie_form = RateMovieForm()    
    movie_to_update = db.get_or_404(Movie,id)
    if request.method == 'POST':
        if rate_movie_form.validate_on_submit():
            new_rating = rate_movie_form.rating.data
            new_review = rate_movie_form.review.data            
            movie_to_update.rating = new_rating
            movie_to_update.review = new_review         
            
            db.session.commit()
            return redirect(url_for('home'))
        return "Movie details cannot be updated" 
    return render_template("edit.html", movie=movie_to_update, form=rate_movie_form)   

@app.route("/delete",methods=["GET"] )
def delete():
    id = request.args.get('id')       
    movie_to_delete = db.get_or_404(Movie,id)    
    db.session.delete(movie_to_delete)        
    db.session.commit()
    return redirect(url_for('home'))        

@app.route("/add_movie",methods=["GET", "POST"] )     
def get_movie_detail():    
    movie_id = request.args.get('id')
    print(f"movie_id: {movie_id}")
    rate_movie_form = RateMovieForm()
     
    if request.method == 'GET':                 
        url = f"{tmdb_detail_url}/{movie_id}"
        parameter = {                
            'api_key' : API_KEY
        }
        response = requests.get(url=url, params=parameter)
        details = response.json()
        title = details['title']
        year = details['release_date']        
        description = details['overview']  
        img_url = f"https://www.themoviedb.org/t/p/original{details['poster_path']}"
        # default value for rating, ranking, review - edit later
        rating = 1.0
        ranking = 5
        review = "Good"
        print(f"details are: {title,year,description,img_url}")
        movie = Movie(title=title,year=year,description=description,img_url=img_url,rating=rating,ranking=ranking,review=review)
        db.session.add(movie)
        db.session.commit()         
        movie_to_update = db.session.execute(db.select(Movie).where(Movie.title == title)).scalar()   
        return redirect(url_for("edit_rating", id=movie_to_update.id))
    return redirect(url_for('home')) 
    



if __name__ == "__main__":
    app.run(debug=True)
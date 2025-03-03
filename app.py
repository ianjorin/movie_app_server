from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape
from movie import get_popular_movies, get_movie_details
import os
from db_models import User, Rating, db
from dotenv import load_dotenv
from sqlalchemy import text, select
from sqlalchemy.orm import DeclarativeBase
from flask_login import (
    login_required,
    LoginManager,
    login_user,
    logout_user,
    current_user,
)
from flask_bcrypt import Bcrypt
import datetime
import werkzeug
from flask_cors import CORS


load_dotenv()


app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.secret_key = os.environ.get("SECRET_KEY")


bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


db.init_app(app)

with app.app_context():
    db.create_all()


# route to handle user signup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        data = request.get_json()
        username = data["username"]
        if User.query.filter_by(username=username).first():
            error_message = "User already exists"
            # return render_template("signup.html", error_message=error_message)
            return jsonify(
                {
                    "status": "error",
                    "message": "User already exists",
                }
            )
        else:
            # password = request.form["password"]
            # password = bcrypt.generate_password_hash(password).decode("utf-8")
            user = User(username=username)
            db.session.add(user)
            db.session.commit()
            # login_user(user)
            # return redirect(url_for("index"))
            return jsonify(
                {
                    "status": "success",
                    "message": "User signed up successfully",
                    "data": {"username": user.username, "user_id": user.id},
                }
            )
    # return render_template("signup.html")
    return jsonify(
        {
            "status": "error",
            "message": "Try logging in again",
        }
    )


# route to handle user login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        username = data["username"]
        user = User.query.filter_by(username=username).first()
        if user:
            # login_user(user)
            # return redirect(url_for("index"))
            return jsonify(
                {
                    "status": "success",
                    "message": "User logged in successfully",
                    "data": {"username": user.username, "user_id": user.id},
                }
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "message": "User does not exist",
                }
            )
    return jsonify(
        {
            "status": "error",
            "message": "Try logging in again",
        }
    )


# route used to logout user
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


# handler for bad requests
# @app.errorhandler(werkzeug.exceptions.BadRequest)
# def handle_bad_request(exception):
#     print(exception.code)
#     print(exception.description)
#     return render_template("index.html", movie=None)


# protected route to display movie details to logged in user
@app.route("/<int:user_id>", methods=["GET", "POST"])
@app.route("/<int:user_id>/<int:movie_id>", methods=["GET", "POST"])
# @login_required
def index(movie_id=None, user_id=None):
    if request.method == "POST":
        data = request.get_json()
        user_id = user_id
        rating = data["rating"]
        comment = data["comment"]
        movie_id = data["movie_id"]
        created_at = datetime.datetime.now()
        user = User.query.filter_by(id=user_id).first()
        rating = Rating(
            user_id=user_id,
            movie_id=movie_id,
            rating=rating,
            comment=comment,
            created_at=created_at,
        )
        db.session.add(rating)
        db.session.commit()
        return jsonify(
            {
                "status": "success",
                "message": "Rating added successfully",
                "data": {
                    "rating": rating.rating,
                    "comment": rating.comment,
                    "created_at": rating.created_at,
                    "id": rating.id,
                    "username": user.username,
                },
            }
        )
    if movie_id is None:
        movie_id = get_popular_movies()
    else:
        movie_id = movie_id
    data = get_movie_details(movie_id)
    rating = db.session.execute(
        select(Rating, User).join(User).where(Rating.movie_id == movie_id)
    )
    user_id = user_id
    data = dict(data)
    others_ratings = []
    user_ratings = []
    for rating in rating:
        if rating[1].id != user_id:
            others_ratings.append(
                {
                    "rating": rating[0].rating,
                    "comment": rating[0].comment,
                    "created_at": rating[0].created_at,
                    "id": rating[0].id,
                    "username": rating[1].username,
                }
            )
        else:
            user_ratings.append(
                {
                    "rating": rating[0].rating,
                    "comment": rating[0].comment,
                    "created_at": rating[0].created_at,
                    "id": rating[0].id,
                    "username": rating[1].username,
                }
            )

    # print(rating)
    if data is None:
        # return render_template("index.html", movie=None)
        return jsonify(
            {
                "status": "error",
                "message": "Movie not found at this time Try again later",
            }
        )
    # return render_template("index.html", movie=data, results=rating)
    return jsonify(
        {
            "status": "success",
            "data": {
                "movie": data,
                "ratings": others_ratings,
                "user_ratings": user_ratings,
            },
        }
    )


# delete a rating by id
@app.route("/delete/<int:id>", methods=["DELETE"])
def delete_rating(id):
    try:
        rating = Rating.query.filter_by(id=id).first()
        db.session.delete(rating)
        db.session.commit()
        return jsonify({"status": "success", "message": "Rating deleted successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Rating not found"})


# update a rating by id
@app.route("/update/<int:id>", methods=["PUT"])
def update_rating(id):
    try:
        data = request.get_json()
        rating = Rating.query.filter_by(id=id).first()
        rating.rating = data["rating"]
        rating.comment = data["comment"]
        db.session.commit()
        return jsonify({"status": "success", "message": "Rating updated successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": "Rating not found"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=os.environ.get("PORT", 3090))

import requests
import os
import random
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
image_size = "w400"
image_base_url = f"https://image.tmdb.org/t/p/{image_size}"

popular_movies = [1241982, 822119, 939243, 927342, 1160956]


# helper function to return a random popular movie id
def get_popular_movies():
    rand_index = random.randint(0, len(popular_movies) - 1)
    return popular_movies[rand_index]


# function to get movie details using id
def get_movie_details(movie_id):

    if movie_id is None:
        return None

    response = requests.get(
        f"https://api.themoviedb.org/3/movie/{movie_id}",
        params={
            "api_key": API_KEY,
            "language": "en-US",
        },
    )
    if response.status_code == 200:
        data = response.json()
        name = data["title"]
        description = data["overview"]
        release_date = data["release_date"]
        poster_path = data["poster_path"]
        movie_image = image_base_url + poster_path
        genre = [genre["name"] for genre in data["genres"]]
        wiki = get_movie_wiki(name)

        movie_details = {
            "id": movie_id,
            "name": name,
            "description": description,
            "release_date": release_date,
            "movie_image": movie_image,
            "genre": genre,
            "wiki": wiki,
        }
        return movie_details

    else:
        print("Error:", response.status_code)
        return None


# this function gets the base url for movie images
def get_api_config():
    response = requests.get(
        f"https://api.themoviedb.org/3/configuration?api_key={API_KEY}"
    )
    if response.status_code == 200:
        data = response.json()
        return data["images"]["secure_base_url"]

    else:
        print("Error:", response.status_code)
        return None


# function to get movie wiki page
def get_movie_wiki(movie_name):
    if movie_name is None:
        return None

    response = requests.get(
        f"https://en.wikipedia.org/w/api.php?format=json&action=query&titles={movie_name}"
    )
    if response.status_code == 200:
        data = response.json()
        title = list(data["query"]["pages"].values())[0]["title"]
        title = title.replace(" ", "_")
        wiki_url = f"https://en.wikipedia.org/wiki/{title}"
        return wiki_url
    else:
        print("Error:", response.status_code)
        return None


# if __name__ == "__main__":
#     movie_id = get_popular_movies()
#     movie_details = get_movie_details(movie_id)
#     print(get_movie_wiki(movie_details['name']))

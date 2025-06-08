import pickle
import pandas as pd
import streamlit as st
import requests
import time

# Load movie data and convert dict to DataFrame
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

# Load similarity matrix
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Create cleaned title column for safe matching
movies['title_clean'] = movies['title'].str.strip().str.lower()

# Cache dictionary to store poster URLs and avoid repeated API calls
poster_cache = {}

def fetch_poster(movie_id, retries=3, backoff=1):
    if movie_id in poster_cache:
        return poster_cache[movie_id]

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=29bb5b892476d8848b973e35eba8446b&language=en-US"

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()  # Raise error for bad responses
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                full_path = f"https://image.tmdb.org/t/p/w500{poster_path}"
            else:
                full_path = "https://via.placeholder.com/500x750?text=No+Image"
            poster_cache[movie_id] = full_path
            return full_path
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(backoff)  # wait before retry
                backoff *= 2  # exponential backoff
            else:
                print(f"Failed to fetch poster for movie ID {movie_id}: {e}")
                full_path = "https://via.placeholder.com/500x750?text=No+Image"
                poster_cache[movie_id] = full_path
                return full_path

def recommend(movie):
    movie_clean = movie.strip().lower()
    matching_movies = movies[movies['title_clean'] == movie_clean]

    if matching_movies.empty:
        st.error(f"Movie '{movie}' not found in database!")
        return [], []

    index = matching_movies.index[0]

    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:11]:
        movie_id = movies.iloc[i[0]].movie_id
        movie_title = movies.iloc[i[0]].title
        poster_url = fetch_poster(movie_id)

        recommended_movie_names.append(movie_title)
        recommended_movie_posters.append(poster_url)

    return recommended_movie_names, recommended_movie_posters

# Streamlit UI
st.header('🎬 Movie Recommender System')

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

    if recommended_movie_names:
        cols = st.columns(len(recommended_movie_names))
        for idx, col in enumerate(cols):
            with col:
                st.image(recommended_movie_posters[idx])
                st.text(recommended_movie_names[idx])

import streamlit as st
import pickle
import requests
import base64
import time
from urllib.parse import quote_plus
import concurrent.futures

# 1) SETTING THE FULL SCREEN BACKGROUND IMAGE
def set_bg_local(image_file):
    with open(image_file, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode()
    page_bg_img = f"""
    <style>
    .stApp {{
        background: url("data:image/png;base64,{encoded_string}") no-repeat center center fixed;
        background-size: cover;
        min-height: 100vh;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_bg_local("background.jpg")  # Ensure "background.jpg" is in the same folder

# 2) LOAD MOVIE DATA
movies = pickle.load(open('mov.pkl', 'rb'))
simi = pickle.load(open('simi.pkl', 'rb'))
mov_list = movies['title'].values

# 3) GLOBAL STYLES (HIGH CONTRAST FOR DARK BG)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }
    .main-title {
        color: #FFFDE7;
        font-size: 52px;
        font-family: 'Poppins', sans-serif;
        font-weight: 800;
        margin-bottom: 20px;
        letter-spacing: 2px;
        text-shadow: 2px 2px 16px #000, 0 0 8px #00FFF0;
        text-align: center;
    }
    .movie-title {
        font-size: 30px;
        font-weight: 800;
        color: #FFFF00;
        font-family: 'Poppins', sans-serif;
        margin: 32px 0 18px 0;
        text-shadow: 1px 1px 8px #000;
        text-align: center;
    }
    .stSelectbox > div {
        background: rgba(30,30,30,0.98) !important;
        color: #00FFFF !important;
        font-size: 18px !important;
        border-radius: 10px !important;
        border: 2px solid #FFFF00 !important;
        margin-bottom: 15px !important;
        font-weight: 700 !important;
    }
    .stSelectbox label {
        color: #FFFDE7 !important;
        font-size: 20px !important;
        font-weight: 700 !important;
    }
    .stButton button {
        background: linear-gradient(90deg, #FF00FF 0%, #00FFFF 100%);
        color: #222;
        border: none;
        border-radius: 12px;
        padding: 0.7em 2.2em;
        font-size: 20px;
        font-weight: 800;
        margin: 18px 0 12px 0;
        box-shadow: 0 4px 24px 0 rgba(72,0,120,0.10);
        transition: all 0.2s;
        letter-spacing: 1px;
        text-shadow: 1px 1px 6px #FFF;
    }
    .stButton button:hover {
        background: linear-gradient(90deg, #FFFF00 0%, #00FFFF 100%);
        color: #000;
        transform: scale(1.04);
        box-shadow: 0 6px 32px 0 rgba(72,0,120,0.18);
    }
    .poster {
        border-radius: 16px;
        transition: transform 0.3s cubic-bezier(.25,.8,.25,1), box-shadow 0.3s;
        cursor: pointer;
        width: 100%;
        max-width: 220px;
        height: 330px;
        object-fit: cover;
        margin-bottom: 8px;
        box-shadow: 0 4px 24px 0 rgba(0,0,0,0.25);
        border: 2px solid #00FFFF;
    }
    .poster:hover {
        transform: scale(1.07) rotate(-2deg);
        box-shadow: 0 8px 32px 0 rgba(72,0,120,0.28);
        border: 2px solid #FFFF00;
    }
    .rec-movie-caption {
        color: #FFFF00;
        font-size: 20px;
        margin-top: 8px;
        font-weight: 800;
        text-shadow: 2px 2px 6px #000, 0 0 4px #FFF;
        text-align: center;
        letter-spacing: 1px;
    }
    /* Hide Streamlit default header/footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 4) MAIN INTERFACE
st.markdown("<h1 class='main-title'>🎬 Movie Recommender System</h1>", unsafe_allow_html=True)

option = st.selectbox(
    '🎥 Select a movie:',
    mov_list,
    help="Choose a movie to get recommendations",
    format_func=lambda x: f"🍿 {x}",
)

# 5) HELPER FUNCTIONS (NO CACHE, PARALLELIZED)
def fetchpos_fast(mov_id, retries=3, delay=0.2):
    url = f'https://api.themoviedb.org/3/movie/{mov_id}?api_key=2a41f9b3c327106788d96924b3c0349f&language=en-US'
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return "https://image.tmdb.org/t/p/w500/" + poster_path
            else:
                return ""
        except requests.exceptions.RequestException:
            if attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))
                continue
            else:
                return ""

def recommend_fast(movie):
    if movie not in movies['title'].values:
        return [], []
    movie_index = movies[movies['title'] == movie].index[0]
    distances = simi[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:5]
    mov_ids = [movies.iloc[i[0]].movie_id for i in movies_list]
    rec_mov = [movies.iloc[i[0]].title for i in movies_list]

    # Fetch posters in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        recpos = list(executor.map(fetchpos_fast, mov_ids))

    return rec_mov, recpos

# 6) RECOMMEND BUTTON & RESULTS
placeholder_url = "https://upload.wikimedia.org/wikipedia/commons/f/fc/No_picture_available.png"

if st.button('🔍 Recommend Movies'):
    list_mov, posters = recommend_fast(option)
    if list_mov:
        st.markdown(
            f"<h2 class='movie-title'>Recommended Movies for '{option}'</h2>",
            unsafe_allow_html=True
        )
        cols = st.columns(len(posters))
        for i, col in enumerate(cols):
            with col:
                poster_url = posters[i] if posters[i] else placeholder_url
                search_query = quote_plus(list_mov[i] + " movie")
                search_url = f"https://www.google.com/search?q={search_query}"
                st.markdown(
                    f"<a href='{search_url}' target='_blank'>"
                    f"<img src='{poster_url}' class='poster'/>"
                    f"</a>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div class='rec-movie-caption'>{list_mov[i]}</div>",
                    unsafe_allow_html=True
                )

# 7) OPTIONAL: FOOTER OR BADGE
st.markdown(
    """
    <div style='text-align:center; margin-top:32px;'>
        <span style='color: #FFFDE7; font-size:14px; opacity:0.85;'>
            Made with ❤️ using Streamlit
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

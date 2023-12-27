import os
import io
import zipfile
from flask import Flask, render_template, redirect, flash, request, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash
from config import YOUTUBE_API_KEY, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import googleapiclient.discovery
from pytube import YouTube
from pytube.cli import on_progress

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "secret_key"

# Set the path to the downloads folder
app.config["DOWNLOADS_FOLDER"] = os.path.join(app.root_path, "downloads")

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# Initialize Spotipy with client credentials flow
sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET
    )
)

API_KEY = YOUTUBE_API_KEY


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

    # Define a many-to-many relationship with songs a user downloaded
    downloaded_songs = db.relationship(
        "Song", secondary="user_song", back_populates="downloaded_by"
    )

    playlists = db.relationship("Playlist", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Define a one-to-many relationship with songs
    songs = db.relationship("Song", backref="playlist", lazy=True)


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    youtube_url = db.Column(db.String(255), nullable=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey("playlist.id"), nullable=True)

    # Define a many-to-many relationship with users who downloaded the song
    downloaded_by = db.relationship(
        "User", secondary="user_song", back_populates="downloaded_songs"
    )


class UserSong(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey("song.id"), primary_key=True)


@login_manager.user_loader
def load_user(user_id):
    # Load a user from the database based on the user_id
    return User.query.get(int(user_id))


# Define RegistrationForm
class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=4, max=80)]
    )
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


# Define LoginForm
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


# Define routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    playlist_songs = []  # Initialize playlist_songs with an empty list
    playlist_id = None

    if request.method == "POST":
        # Get the Spotify playlist link from the form
        spotify_link = request.form.get("spotify_link")

        # Check if the link is a valid Spotify playlist URL
        if spotify_link.startswith("https://open.spotify.com/playlist/"):
            # Extract the playlist ID without the query string
            playlist_id = spotify_link.split("/")[-1].split("?")[0]

        if playlist_id:
            flash("Spotify playlist link is valid. Fetching songs...", "success")

            # Process the link and get playlist songs
            playlist_songs = get_playlist_songs(playlist_id, playlist_songs)

            if not playlist_songs:
                flash(
                    "Failed to fetch songs from the Spotify playlist. Want to try again?",
                    "error",
                )
            else:
                # Pass the downloads_folder to download_mp3 function
                for song in playlist_songs:
                    yt_url = search_yt_url(
                        song["title"], song["artist"], app.config["DOWNLOADS_FOLDER"]
                    )
                    download_successful = download_mp3(
                        yt_url,
                        song["title"],
                        song["artist"],
                        app.config["DOWNLOADS_FOLDER"],
                    )

                    if download_successful:
                        flash(
                            f'Successfully fetched {song["title"]} by {song["artist"]}',
                            "success",
                        )
                    else:
                        flash(
                            f'Failed to fetch {song["title"]} by {song["artist"]}',
                            "error",
                        )
        else:
            flash(
                "Invalid Spotify playlist link. Please check if what you have is a valid playlist link.",
                "error",
            )

    # Load downloaded songs for the user
    downloaded_songs = current_user.downloaded_songs

    return render_template(
        "dashboard.html",
        playlist_songs=playlist_songs,
        downloaded_songs=downloaded_songs,
    )


def create_downloads_folder(app):
    # Define the path to the downloads folder
    downloads_folder = os.path.join(app.root_path, "downloads")

    # Check if the downloads folder exists, and create it if not
    if not os.path.exists(downloads_folder):
        os.makedirs(downloads_folder)

    return downloads_folder


# functions used by dashboard
def get_playlist_songs(playlist_id, playlist_songs):
    try:
        # Retrieve all tracks from the playlist
        playlist = sp.playlist(
            playlist_id, fields="name,tracks.items(track(name,artists(name),album(id)))"
        )

        if "name" not in playlist:
            raise ValueError("Playlist name not found in Spotify data.")

        playlist_name = playlist["name"]

        # Check if a playlist with the same name already exists for the current user
        existing_playlist = Playlist.query.filter_by(
            name=playlist_name, user=current_user
        ).first()

        if existing_playlist:
            # Use the existing playlist
            new_playlist = existing_playlist
        else:
            # Create a new playlist
            new_playlist = Playlist(name=playlist_name, user=current_user)
            db.session.add(new_playlist)
            db.session.commit()

        tracks = playlist["tracks"]["items"]

        existing_song = None  # Initialize the variable outside of the loop

        for item in tracks:
            title = item["track"]["name"]
            artist = ", ".join([artist["name"] for artist in item["track"]["artists"]])

            # Fetch the album cover URL for the song
            album_id = item["track"]["album"]["id"]
            album_cover_url = get_album_cover_url(album_id)

            # Check if a song with the same title and artist already exists
            existing_song = Song.query.filter_by(
                title=title, artist=artist, playlist=new_playlist
            ).first()

            if existing_song:
                # Use the existing song
                new_song = existing_song
            else:
                # Create a new song
                new_song = Song(title=title, artist=artist, playlist=new_playlist)
                db.session.add(new_song)
                db.session.commit()  # Commit after creating the new song to obtain the song_id

                # Create a new UserSong entry to relate the user with the song
                user_song = UserSong(user_id=current_user.id, song_id=new_song.id)
                db.session.add(user_song)

            # Append the song data to the playlist_songs list
            playlist_songs.append(
                {"title": title, "artist": artist, "album_cover_url": album_cover_url}
            )

        # Commit changes after processing all the songs
        db.session.commit()

        return playlist_songs
    except Exception as e:
        print("Error fetching playlist songs from Spotify, wanna try again?")
        print(f"{str(e)}")
        return None


def get_album_cover_url(album_id):
    try:
        # Get album details using the Spotipy library
        album_data = sp.album(album_id)

        # Get the URL of the first image in the album's images list (usually the largest one)
        if "images" in album_data and len(album_data["images"]) > 0:
            return album_data["images"][0]["url"]
        else:
            # If the album cover URL is not found, you can return a default URL or handle it as needed
            return "URL_TO_DEFAULT_ALBUM_COVER"
    except Exception as e:
        # Handle exceptions as needed
        print(f"Error fetching album cover: {str(e)}")
        return "URL_TO_DEFAULT_ALBUM_COVER"


def check_if_file_exists(title, artist, downloads_folder):
    # Construct the expected MP3 filename
    mp3_filename = f"{title} by {artist}.mp3"
    mp3_filepath = os.path.join(downloads_folder, mp3_filename)

    # Check if the MP3 file already exists in the downloads folder
    if os.path.exists(mp3_filepath):
        return mp3_filepath  # Return the local file path

    return None  # Return None if the file does not exist


def search_yt_url(song_title, artist_name, downloads_folder):
    mp3_filepath = check_if_file_exists(song_title, artist_name, downloads_folder)

    if mp3_filepath:
        return mp3_filepath

    # If the file doesn't exist, perform the YouTube API search
    else:
        yt = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)

        # Construct the search query
        query = f"{song_title} by {artist_name} music video"

        # Make the API request
        search_response = (
            yt.search().list(q=query, type="video", part="id", maxResults=1).execute()
        )

        # Get the first video result
        video_id = search_response.get("items")[0]["id"]["videoId"]

        # Construct the YouTube URL
        yt_url = f"https://www.youtube.com/watch?v={video_id}"

        return yt_url


def download_mp3(yt_url, title, artist, downloads_folder):
    mp3_filename = f"{title} by {artist}.mp3"
    mp3_filepath = check_if_file_exists(title, artist, downloads_folder)

    if mp3_filepath:
        print(f"{mp3_filepath} already exists. Skipping download.")
        return True

    try:
        yt = YouTube(yt_url, on_progress_callback=on_progress)
        stream = yt.streams.filter(only_audio=True).first()

        if stream:
            stream.download(output_path=downloads_folder, filename=mp3_filename)
            return True
        else:
            print(f"No audio stream available for {yt.title}")
            return False
    except Exception as e:
        print(f"Error downloading or converting to MP3: {str(e)}")
        return False


@app.route("/download_selected_songs", methods=["POST"])
@login_required
def download_selected_songs():
    selected_songs = request.form.getlist("selected_songs")

    # Filter out any empty values
    selected_songs = [song for song in selected_songs if song]

    # List to store the paths of the selected songs
    song_paths = []

    for song_info in selected_songs:
        title, artist = song_info.split("|")
        song_path = os.path.join(
            app.config["DOWNLOADS_FOLDER"], f"{title} by {artist}.mp3"
        )
        song_paths.append(song_path)

    # ZIP archive containing the selected songs
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for song_path in song_paths:
            # Add each song to the ZIP archive
            zipf.write(song_path, os.path.basename(song_path))

    # Seek to the beginning of the ZIP buffer
    zip_buffer.seek(0)

    # Generate a response with the ZIP file
    response = send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="selected_songs.zip",
    )

    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if a user with the same username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for("index"))

        # If username is unique, add new user to the database
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash(
                "Invalid username or password. Please try again.", "error"
            )  # Flash error if login fails

    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# Run the app
if __name__ == "__main__":
    with app.app_context():
        create_downloads_folder(app)
        db.create_all()
    app.run(debug=True)

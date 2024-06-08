# this is where pages are stored

from flask import Blueprint, render_template

views = Blueprint('views', __name__)

# premade playlists
# connect to db later
playlists = {
    1: {"name": "Rap music", "song_id": ["7dAjrcykxdDA87r4zPUTEU", "3v9T97LAIV0deXJrZJ9NcI", "5Ng31FBZTbKPQxl88gEQbr"], "creator_id": 1},
    2: {"name": "Rnb hits", "song_id": ["11WuptzKtcVfPMYaf5aook", "5Y77SQxEr1eiofPeUTPHxM", "5j0McHPthKpOXRr3fBq8M0"], "creator_id": 1},
    3: {"name": "Pop music", "song_id": ["2VxeLyX666F8uXCJ0dZF8B", "4TnjEaWOeW0eKTKIEvJyCa", "5QO79kh1waicV47BqGRL3g"], "creator_id": 1},
    4: {"name": "Rock music", "song_id": ["1ZwdS5xdxEREPySFridCfh", "1ZwdS5xdxEREPySFridCfh", "1ZwdS5xdxEREPySFridCfh"], "creator_id": 1},
    5: {"name": "Country music", "song_id": ["4bHsxqR3GMrXTxEPLuK5ue", "4bHsxqR3GMrXTxEPLuK5ue", "4bHsxqR3GMrXTxEPLuK5ue"], "creator_id": 1},
}


@ views.route('/')
def home():
    return render_template("home.html")


@ views.route('/browse')
def browse():
    return render_template('browse.html', playlists=playlists)


@ views.route('/vplaylist/<int:playlist_id>')
def vplaylist(playlist_id):
    playlist = playlists.get(playlist_id)
    if playlist is None:
        return "Playlist not found", 404
    return render_template('viewplaylist.html', playlist=playlist)


@ views.route('/playlist')
def playlist():
    return render_template("playlist.html")

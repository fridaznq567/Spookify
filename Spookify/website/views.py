from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from .models import User, Playlist, Song, PlaylistSong, Follow
from . import db
from sqlalchemy import text

views = Blueprint('views', __name__)


@views.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user)


@views.route('/create-playlist', methods=['GET', 'POST'])
@login_required
def create_playlist():
    if request.method == 'POST':
        playlist_name = request.form.get('playlistName')
        use_generator = 'useGenerator' in request.form

        # Create the playlist using raw SQL
        create_playlist_sql = text("""
            INSERT INTO playlist (name, user_id) VALUES (:name, :user_id) RETURNING id;
        """)
        result = db.engine.execute(create_playlist_sql, {
                                   'name': playlist_name, 'user_id': current_user.id})
        playlist_id = result.fetchone()[0]

        if use_generator:
            mood = request.form.get('mood')
            tempo = request.form.get('tempo')
            lyrics = request.form.get('lyrics')

            # Building the filtering query based on user input
            query_parts = ["SELECT * FROM song WHERE 1=1"]
            params = {}

            if mood == 'happy':
                query_parts.append("AND valence > 0.5")
            elif mood == 'sad':
                query_parts.append("AND valence < 0.5")

            if tempo == 'fast':
                query_parts.append("AND tempo > 120")
            elif tempo == 'slow':
                query_parts.append("AND tempo < 120")

            if lyrics == 'many':
                query_parts.append("AND speechiness > 0.33")
            elif lyrics == 'instruments':
                query_parts.append("AND speechiness < 0.33")

            # Add randomization to shuffle results and limit to 20 songs
            query_parts.append("ORDER BY RANDOM()")
            query_parts.append("LIMIT 20")
            final_query = " ".join(query_parts)
            filter_songs_sql = text(final_query)

            # Execute the filtering query
            result = db.engine.execute(filter_songs_sql, params)
            songs = result.fetchall()

            # Add songs to the playlist using raw SQL
            add_song_to_playlist_sql = text("""
                INSERT INTO playlist_song (playlist_id, song_id) VALUES (:playlist_id, :song_id)
            """)
            for song in songs:
                db.engine.execute(add_song_to_playlist_sql, {
                                  'playlist_id': playlist_id, 'song_id': song.id})

        flash('Playlist created successfully!', 'success')
        return redirect(url_for('views.playlists'))

    return render_template('create_playlist.html')


@views.route('/playlists', methods=['GET'])
@login_required
def playlists():
    user_playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return render_template('playlists.html', playlists=user_playlists)


@views.route('/delete-playlist/<int:playlist_id>', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    # Ensure the playlist belongs to the current user
    check_playlist_sql = text(
        "SELECT * FROM playlist WHERE id = :playlist_id AND user_id = :user_id")
    result = db.engine.execute(
        check_playlist_sql, {'playlist_id': playlist_id, 'user_id': current_user.id})
    playlist = result.fetchone()
    if not playlist:
        flash('Playlist not found or you do not have permission to delete it.', 'danger')
        return redirect(url_for('views.playlists'))

    # Delete associated playlist_song entries
    delete_playlist_songs_sql = text(
        "DELETE FROM playlist_song WHERE playlist_id = :playlist_id")
    db.engine.execute(delete_playlist_songs_sql, {'playlist_id': playlist_id})

    # Delete the playlist
    delete_playlist_sql = text("DELETE FROM playlist WHERE id = :playlist_id")
    db.engine.execute(delete_playlist_sql, {'playlist_id': playlist_id})

    flash('Playlist deleted successfully!', 'success')
    return redirect(url_for('views.playlists'))


@views.route('/search')
@login_required
def search():
    query = request.args.get('query', '')
    if query:
        try:
            search_results = Song.query.filter(
                Song.song_name.contains(query)).all()
            return render_template('search_results.html', query=query, songs=search_results)
        except Exception as e:
            flash('An error occurred during the search. Please try again.', 'danger')
            return redirect(url_for('views.home'))
    else:
        return redirect(url_for('views.home'))


@views.route('/suggest')
@login_required
def suggest():
    q = request.args.get('q', '')
    suggestions = []
    if q:
        suggestions = [song.song_name for song in Song.query.filter(
            Song.song_name.contains(q)).limit(5).all()]
    return jsonify(suggestions)


@views.route('/song/<song_id>')
@login_required
def song_details(song_id):
    song = Song.query.get_or_404(song_id)
    playlists = Playlist.query.filter_by(
        user_id=current_user.id).all()  # Fetch user playlists
    return render_template('song_details.html', song=song, playlists=playlists)


@views.route('/add-to-playlist/<song_id>', methods=['POST'])
@login_required
def add_to_playlist(song_id):
    playlist_id = request.form.get('playlist_id')
    if not playlist_id:
        flash('No playlist selected!', 'danger')
        return redirect(url_for('views.song_details', song_id=song_id))

    # Check if the playlist exists
    check_playlist_sql = text("SELECT * FROM playlist WHERE id = :playlist_id")
    result = db.engine.execute(check_playlist_sql, playlist_id=playlist_id)
    playlist = result.fetchone()
    if not playlist:
        flash('Playlist not found!', 'danger')
        return redirect(url_for('views.song_details', song_id=song_id))

    # Check if the song exists
    check_song_sql = text("SELECT * FROM song WHERE id = :song_id")
    result = db.engine.execute(check_song_sql, song_id=song_id)
    song = result.fetchone()
    if not song:
        flash('Song not found!', 'danger')
        return redirect(url_for('views.song_details', song_id=song_id))

    # Check if the song is already in the playlist
    check_playlist_song_sql = text("""
        SELECT * FROM playlist_song WHERE playlist_id = :playlist_id AND song_id = :song_id
    """)
    result = db.engine.execute(
        check_playlist_song_sql, playlist_id=playlist_id, song_id=song_id)
    playlist_song = result.fetchone()
    if playlist_song:
        flash('Song already in playlist!', 'danger')
        return redirect(url_for('views.song_details', song_id=song_id))

    # Add the song to the playlist
    add_playlist_song_sql = text("""
        INSERT INTO playlist_song (playlist_id, song_id) VALUES (:playlist_id, :song_id)
    """)
    db.engine.execute(add_playlist_song_sql,
                      playlist_id=playlist_id, song_id=song_id)

    flash('Song added to playlist!', 'success')
    return redirect(url_for('views.song_details', song_id=song_id))


@views.route('/browse', methods=['GET'])
@login_required
def browse():
    genre = request.args.get('genre', '')
    valence = request.args.get('valence', '')
    tempo = request.args.get('tempo', '')

    # Building the filtering query based on user input
    query_parts = ["SELECT * FROM song WHERE 1=1"]
    params = {}

    if genre:
        query_parts.append("AND genre = :genre")
        params['genre'] = genre

    if valence == 'high':
        query_parts.append("AND valence > 0.5")
    elif valence == 'low':
        query_parts.append("AND valence < 0.5")

    if tempo == 'fast':
        query_parts.append("AND tempo > 120")
    elif tempo == 'medium':
        query_parts.append("AND tempo BETWEEN 90 AND 120")
    elif tempo == 'slow':
        query_parts.append("AND tempo < 90")

    final_query = " ".join(query_parts)
    filter_songs_sql = text(final_query)

    # Execute the filtering query
    result = db.engine.execute(filter_songs_sql, params)
    songs = result.fetchall()

    # Fetch distinct genres
    distinct_genres_sql = text("SELECT DISTINCT genre FROM song")
    result = db.engine.execute(distinct_genres_sql)
    genres = [row['genre'] for row in result]

    return render_template('browse.html', songs=songs, genres=genres)


@views.route('/users')
@login_required
def users():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('users.html', users=users)


@views.route('/user/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    playlists = Playlist.query.filter_by(user_id=user.id).all()

    # Determine the most common genre
    genre_counts = db.session.query(Song.genre, func.count(Song.genre)).join(PlaylistSong).join(Playlist).filter(
        Playlist.user_id == user.id).group_by(Song.genre).order_by(func.count(Song.genre).desc()).all()
    most_common_genre = genre_counts[0][0] if genre_counts else None

    followed_users = [follow.followed for follow in user.followed]

    # Find common songs
    user_playlist_songs = db.session.query(Song.id).join(PlaylistSong).join(
        Playlist).filter(Playlist.user_id == user.id).subquery()
    current_user_playlist_songs = db.session.query(Song).join(PlaylistSong).join(Playlist).filter(
        Playlist.user_id == current_user.id, PlaylistSong.song_id.in_(user_playlist_songs)).all()

    return render_template('user_profile.html', user=user, playlists=playlists, followed_users=followed_users, most_common_genre=most_common_genre, common_songs=current_user_playlist_songs)


@views.route('/follow/<int:user_id>')
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot follow yourself!', 'danger')
        return redirect(url_for('views.users'))

    follow = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=user.id).first()
    if follow:
        flash('You are already following this user!', 'danger')
    else:
        follow = Follow(follower_id=current_user.id, followed_id=user.id)
        db.session.add(follow)
        db.session.commit()
        flash(f'You are now following {user.name}!', 'success')

    return redirect(url_for('views.user_profile', user_id=user.id))


@views.route('/unfollow/<int:user_id>')
@login_required
def unfollow(user_id):
    user = User.query.get_or_404(user_id)
    if user == current_user:
        flash('You cannot unfollow yourself!', 'danger')
        return redirect(url_for('views.users'))

    follow = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=user.id).first()
    if follow:
        db.session.delete(follow)
        db.session.commit()
        flash(f'You have unfollowed {user.name}.', 'success')
    else:
        flash(f'You are not following {user.name}.', 'danger')
    return redirect(url_for('views.user_profile', user_id=user.id))


@views.route('/followed-playlists')
@login_required
def followed_playlists():
    followed_users = [follow.followed for follow in current_user.followed]
    playlists = Playlist.query.filter(Playlist.user_id.in_(
        [user.id for user in followed_users])).all()
    return render_template('followed_playlists.html', playlists=playlists)


@views.route('/playlist/<int:playlist_id>')
@login_required
def view_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    songs = db.session.query(Song).join(PlaylistSong).filter(
        PlaylistSong.playlist_id == playlist_id).all()
    return render_template('view_playlist.html', playlist=playlist, songs=songs)

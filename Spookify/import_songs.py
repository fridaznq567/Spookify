import csv
from website import create_app, db
from website.models import Song

app = create_app()


def import_songs(csv_file):
    with app.app_context():
        with open(csv_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                song_name = row['song_name'].strip()
                if song_name:  # Only add songs with non-empty names
                    if not db.session.query(Song).filter_by(id=row['id']).first():
                        song = Song(
                            id=row['id'],
                            danceability=float(row['danceability']),
                            energy=float(row['energy']),
                            valence=float(row['valence']),
                            # Include speechiness
                            speechiness=float(row['speechiness']),
                            tempo=float(row['tempo']),
                            duration_ms=int(row['duration_ms']),
                            genre=row['genre'],
                            song_name=song_name
                        )
                        db.session.add(song)
            db.session.commit()
            print(f"Songs from {csv_file} have been successfully imported.")


if __name__ == '__main__':
    import_songs(
        r'/Users/fridaalm/Downloads/Spookify/Spookify/dataset_music/genres_v2.csv')
    # Alternatively, use forward slashes:
    # import_songs('C:/Users/willi/Desktop/dis/Spookify/Spookify/Spookify/dataset_music/genres_v2.csv')

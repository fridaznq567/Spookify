from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

class PlaylistForm(FlaskForm):
    mood = SelectField('Mood', choices=[('happy', 'Happy'), ('neutral', 'Neutral'), ('sad', 'Sad')], validators=[DataRequired()])
    tempo = SelectField('Tempo', choices=[('fast', 'Fast'), ('medium', 'Medium'), ('slow', 'Slow')], validators=[DataRequired()])
    lyrics = SelectField('Lyrics', choices=[('mixed', 'Mixed'), ('many', 'Many'), ('instruments', 'Instruments Only')], validators=[DataRequired()])
    playlist_name = StringField('Playlist Name', validators=[DataRequired()])
    submit = SubmitField('Generate')

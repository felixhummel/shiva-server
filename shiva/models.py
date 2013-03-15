# -*- coding: utf-8 -*-
import os

from flask.ext.sqlalchemy import SQLAlchemy

from shiva import utils
from shiva.utils import slugify as do_slug, randstr

db = SQLAlchemy()

__all__ = ('db', 'Artist', 'Album', 'Track')


def slugify(model, field_name):
    """
    Given the instance of a model and a field to slugify, generates a unique
    slug. If a standard one exists in the DB, or the generated slug is
    numeric-only, a hyphen and the object's ID is appended to it to generate a
    unique and alphanumeric one.

    """

    slug = do_slug(getattr(model, field_name, ''))
    if not slug:
        slug = randstr(6)
    try:
        is_int = isinstance(int(slug), int)
    except ValueError:
        is_int = False

    exists = bool(model.__class__.query.filter_by(slug=slug).count())

    if is_int or exists:
        extra = model.pk
        if not extra:
            extra = randstr(6)

        slug += u'-%s' % extra

    return slug


class Artist(db.Model):
    """
    """

    __tablename__ = 'artists'

    pk = db.Column(db.Integer, primary_key=True)
    # TODO: Update the files' ID3 tags when changing this info.
    name = db.Column(db.String(128), nullable=False)
    slug = db.Column(db.String(128), unique=True, nullable=False)
    image = db.Column(db.String(256))
    events = db.Column(db.String(256))

    tracks = db.relationship('Track', backref='artist', lazy='dynamic')

    def __setattr__(self, attr, value):
        if attr == 'name':
            super(Artist, self).__setattr__('slug', slugify(self, 'name'))

        super(Artist, self).__setattr__(attr, value)

    def __repr__(self):
        return '<Artist (%s)>' % self.name


artists = db.Table('albumartists',
    db.Column('artist_pk', db.Integer, db.ForeignKey('artists.pk')),
    db.Column('album_pk', db.Integer, db.ForeignKey('albums.pk'))
)


class Album(db.Model):
    """
    """

    __tablename__ = 'albums'

    pk = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    slug = db.Column(db.String(128), unique=True, nullable=False)
    year = db.Column(db.Integer)
    cover = db.Column(db.String(256))

    tracks = db.relationship('Track', backref='album', lazy='dynamic')

    artists = db.relationship('Artist', secondary=artists,
                              backref=db.backref('albums', lazy='dynamic'))

    def __setattr__(self, attr, value):
        if attr == 'name':
            super(Album, self).__setattr__('slug', slugify(self, 'name'))

        super(Album, self).__setattr__(attr, value)

    def __repr__(self):
        return '<Album (%s)>' % self.name


class Track(db.Model):
    """
    """

    __tablename__ = 'tracks'

    pk = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.Unicode(256), unique=True, nullable=False)
    title = db.Column(db.String(128))
    slug = db.Column(db.String(128), unique=True)
    bitrate = db.Column(db.Integer)
    file_size = db.Column(db.Integer)
    length = db.Column(db.Integer)
    number = db.Column(db.Integer)

    lyrics = db.relationship('Lyrics', backref='track', uselist=False)

    album_pk = db.Column(db.Integer, db.ForeignKey('albums.pk'), nullable=True)
    artist_pk = db.Column(db.Integer, db.ForeignKey('artists.pk'),
                          nullable=True)

    def __init__(self, path):
        if not isinstance(path, unicode):
            raise ValueError('Invalid parameter for Track. Path or File '
                             'expected, got %s' % type(path))

        self.path = path
        self.extension = utils.ext(path)

    def __setattr__(self, attr, value):
        # when setting title, set slug too
        if attr == 'title':
            super(Track, self).__setattr__('slug', slugify(self, 'title'))

        super(Track, self).__setattr__(attr, value)

    def get_path(self):
        if self.path:
            return self.path.encode('utf-8')
        return None

    def __repr__(self):
        return "<Track ('%s')>" % self.title


class Lyrics(db.Model):
    """
    """

    __tablename__ = 'lyrics'

    pk = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(256))

    track_pk = db.Column(db.Integer, db.ForeignKey('tracks.pk'),
                         nullable=False)

    def __repr__(self):
        return "<Lyrics ('%s')>" % self.track.title

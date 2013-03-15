# -*- coding: utf-8 -*-
"""Music indexer for the Shiva-Server API.
Index your music collection and (optionally) retrieve album covers and artist
pictures from Last.FM.

Usage:
    shiva-indexer [-h] [-v] [-q] [--lastfm] [--nometadata]

Options:
    -h, --help    Show this help message and exit
    --lastfm      Retrieve artist and album covers from Last.FM API.
    --nometadata  Don't read file's metadata when indexing.
    -v --verbose  Show debugging messages about the progress.
    -q --quiet    Suppress warnings.
"""
# K-Pg
import logging
from datetime import datetime
import sys

import pylast

from shiva import models as m
from shiva.app import app, db
from shiva.tagger import TaggedFiles

query = db.session.query


class Indexer(object):
    artists = {}
    albums = {}

    def __init__(self, config=None, use_lastfm=False, no_metadata=False, verbose=False, quiet=False):
        self.config = config
        self.use_lastfm = use_lastfm
        self.no_metadata = no_metadata
        self.verbose = verbose
        self.quiet = quiet

        self.session = db.session
        self.media_dirs = config.get('MEDIA_DIRS', [])

        if self.use_lastfm:
            api_key = config['LASTFM_API_KEY']
            self.lastfm = pylast.LastFMNetwork(api_key=api_key)

        if not len(self.media_dirs):
            print("Remember to set the MEDIA_DIRS option, otherwise I don't "
                  'know where to look for.')

        if not len(config.get('ACCEPTED_FORMATS', [])):
            print("Remember to set the ACCEPTED_FORMATS option, otherwise I don't "
                  'know what files are suitable.')

    def get_artist(self, name):
        if name in self.artists:
            return self.artists[name]
        else:
            cover = None
            if self.use_lastfm:
                cover = self.lastfm.get_artist(name).get_cover_image()
            artist = m.Artist(name=name, image=cover)
            self.session.add(artist)
            self.artists[name] = artist

        return artist

    def get_album(self, name, artist, tagged_file):
        if name in self.albums:
            return self.albums[name]
        else:
            release_year = self.get_release_year(tagged_file=tagged_file)
            cover = None
            if self.use_lastfm:
                try:
                    _artist = self.lastfm.get_artist(artist.name)
                    _album = self.lastfm.get_album(_artist, name)
                    release_year = self.get_release_year(lastfm_album=_album, tagged_file=tagged_file)
                    cover = _album.get_cover_image(size=pylast.COVER_EXTRA_LARGE)
                except pylast.WSError, error:
                    #TODO: proper log error
                    print error

            album = m.Album(name=name, year=release_year, cover=cover)
            self.session.add(album)
            self.albums[name] = album

        return album

    def get_release_year(self, lastfm_album=None, tagged_file=None):
        if self.use_lastfm and lastfm_album:
            _date = lastfm_album.get_release_date()
            try:
                return datetime.strptime(_date, '%d %b %Y, %H:%M').year
            except ValueError:
                pass
        return tagged_file.release_year

    def save(self, unicode_path, tagged_file):
        """
        :param unicode_path: Unicode encoded path.
        :type unicode_path: unicode
        :type tagged_file: shiva.tagger.TaggedFile
        """
        if self.verbose:
            print(unicode_path)

        track = m.Track(unicode_path)

        if self.no_metadata:
            self.session.add(track)
            return True

        if not tagged_file.has_essential_tags:
            logging.warn('File missing essential tags: %s' % tagged_file)
            self.session.add(track)
            return True

        artist_model = self.get_artist(tagged_file.artist)
        album_model = self.get_album(tagged_file.album, artist_model, tagged_file)

        if artist_model not in album_model.artists:
            album_model.artists.append(artist_model)

        track.album = album_model
        track.artist = artist_model
        self.session.add(track)

        if self.verbose:
            try:
                print 'Added %s (%s)' % (track, track.get_path())
            except UnicodeDecodeError:
                print 'WARNING bad title for %s' % track.get_path()

        return True

    def run(self):
        for media_dir_object in self.media_dirs:
            for media_dir in media_dir_object.get_dirs():
                tfs = TaggedFiles(media_dir)
                for path, tf in tfs.iteritems():
                    if tf.has_essential_tags:
                        self.save(path, tf)


def main():
    from docopt import docopt
    arguments = docopt(__doc__)

    use_lastfm = arguments['--lastfm']
    no_metadata = arguments['--nometadata']

    if no_metadata:
        use_lastfm = False

    if use_lastfm and not app.config.get('LASTFM_API_KEY'):
        sys.stderr.write('ERROR: You need a Last.FM API key if you set the --lastfm '
              'flag.\n')
        sys.exit(1)

    lola = Indexer(app.config, use_lastfm=use_lastfm, no_metadata=no_metadata, verbose=arguments['--verbose'], quiet=arguments['--quiet'])
    lola.run()

    # Petit performance hack: Every track will be added to the session but they
    # will be written down to disk only once, at the end.
    lola.session.commit()

    print 'Indexed %d tracks in %d albums from %d different artists'%(
        query(m.Track).count(), query(m.Album).count(), query(m.Artist).count())

if __name__ == '__main__':
    main()


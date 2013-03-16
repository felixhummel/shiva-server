import os
import os.path

import mutagen
from mutagen.mp3 import HeaderNotFoundError

from shiva import utils


class TaggedFile(object):
    
    path = None
    
    def __init__(self, path):
        self.path = path
        try:
            self.id3 = mutagen.File(self.path, easy=True)
        except HeaderNotFoundError:
            self.id3 = None

    def __repr__(self):
        return 'TaggedFile <%s>' % self.path

    def _get_stripped_or_none(self, key):
        x = self.id3.get(key, None)
        if isinstance(x, list):
            # TODO support multiple tag values
            x = x[0]
        if x is None:
            return None
        return x.strip()

    def _get_int(self, key):
        value = self._get_stripped_or_none(key)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            return value

    def _set(self, key, value):
        self.id3[key] = value
        self.id3.save()

    def is_valid(self):
        return self.id3 is not None

    def get_path(self):
        return self.path

    def get_artist(self):
        return self._get_stripped_or_none('artist')

    def set_artist(self, name):
        self._set('artist', name)

    artist = property(get_artist, set_artist)

    def get_album(self):
        return self._get_stripped_or_none('album')

    def set_album(self, name):
        self._set('album', name)

    album = property(get_album, set_album)

    def get_release_year(self):
        return self._get_int('date')

    def set_release_year(self, year):
        self._set('date', year)

    release_year = property(get_release_year, set_release_year)

    def get_bitrate(self):
        try:
            return self.id3.info.bitrate
        except AttributeError:
            # flac says >>'StreamInfo' object has no attribute 'bitrate'<<
            return None

    bitrate = property(get_bitrate)

    def get_length(self):
        return self.id3.info.length

    length = property(get_length)

    def get_track_number(self):
        return self._get_int('tracknumber')

    track_number = property(get_track_number)

    def get_title(self):
        title = self._get_stripped_or_none('title')
        if title is None:
            # guess from filename
            # TODO guess file name encoding (else print fails for titles)
            return os.path.splitext(os.path.basename(self.path))[0]
        return title

    title = property(get_title)

    def get_size(self):
        """ Computes the size (in bytes) of the file in filesystem. """
        return os.stat(self.path).st_size

    size = property(get_size)

    @property
    def has_essential_tags(self):
        return self.artist is not None and self.album is not None and self.title is not None


class TaggedFiles(dict):
    known_extensions = ['mp3', 'ogg', 'flac']

    def __init__(self, media_dir):
        for dirpath, dirnames, filenames in os.walk(media_dir):
            audio_files = [f for f in filenames if utils.ext(f) in self.known_extensions]
            for f in audio_files:
                path = os.path.join(dirpath, f).decode('utf-8')
                self[path] = TaggedFile(path)

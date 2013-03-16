# -*- coding: utf-8 -*-
import os
import re
from random import random
from hashlib import md5

import translitcodec

PUNCT_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text):
    """ Generates an ASCII-only slug. """
    if not text:
        return ''
    result = []
    text = text
    for word in PUNCT_RE.split(text.lower()):
        word = word.encode('translit/long')
        if word:
            result.append(word)

    return unicode(u'-'.join(result))


def randstr(length=None):
    if isinstance(length, int) and length < 1:
        return ''

    digest = md5(str(random())).hexdigest()

    if length:
        return digest[:length]

    return digest


def _import(class_path):
    bits = class_path.split('.')
    mod_name = '.'.join(bits[:-1])
    cls_name = bits[-1]

    mod = __import__(mod_name, None, None, cls_name)

    return getattr(mod, cls_name)


class ID3Manager(object):
    def __init__(self, mp3_path):
        import eyed3  # FIXME: Replace ASAP

        self.mp3_path = mp3_path
        self.reader = eyed3.load(mp3_path)

        if not self.reader.tag:
            self.reader.tag = eyed3.id3.Tag()
            self.reader.tag.track_num = (None, None)

        if self.reader.tag.album is None:
            self.reader.tag.album = u''

        if self.reader.tag.artist is None:
            self.reader.tag.artist = u''

        self.reader.tag.save(mp3_path)

    def __getattribute__(self, attr):
        _super = super(ID3Manager, self)
        try:
            _getter = _super.__getattribute__('get_%s' % attr)
        except AttributeError:
            _getter = None
        if _getter:
            return _getter()

        return super(ID3Manager, self).__getattribute__(attr)

    def __setattr__(self, attr, value):
        value = value.strip() if isinstance(value, (str, unicode)) else value
        _setter = getattr(self, 'set_%s' % attr, None)
        if _setter:
            _setter(value)

        super(ID3Manager, self).__setattr__(attr, value)

    def is_valid(self):
        if not self.reader.path:
            return False

        return True

    def get_path(self):
        return self.mp3_path

    def same_path(self, path):
        return path == self.mp3_path

    def get_artist(self):
        return self.reader.tag.artist.strip()

    def set_artist(self, name):
        self.reader.tag.artist = name
        self.reader.tag.save()

    def get_album(self):
        return self.reader.tag.album.strip()

    def set_album(self, name):
        self.reader.tag.album = name
        self.reader.tag.save()

    def get_release_year(self):
        rdate = self.reader.tag.release_date
        return rdate.year if rdate else None

    def set_release_year(self, year):
        self.release_date.year = year
        self.reader.tag.save()

    def get_bitrate(self):
        return self.reader.info.bit_rate[1]

    def get_length(self):
        return self.reader.info.time_secs

    def get_track_number(self):
        return self.reader.tag.track_num[0]

    def get_title(self):
        if not self.reader.tag.title:
            _title = raw_input('Song title: ').decode('utf-8').strip()
            self.reader.tag.title = _title
            self.reader.tag.save()

        return self.reader.tag.title

    def get_size(self):
        """ Computes the size (in bytes) of the file in filesystem. """

        return os.stat(self.reader.path).st_size


import mutagen
from mutagen.mp3 import HeaderNotFoundError


class MutagenID3Manager(object):

    def __init__(self, mp3_path):
        self.mp3_path = mp3_path
        try:
            self.id3 = mutagen.File(mp3_path, easy=True)
        except HeaderNotFoundError:
            self.id3 = None
        pass

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
        return self.mp3_path

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
        return self.id3.info.bitrate

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
            return os.path.splitext(os.path.basename(self.mp3_path))[0]
        return title

    title = property(get_title)

    def get_size(self):
        """ Computes the size (in bytes) of the file in filesystem. """
        return os.stat(self.mp3_path).st_size

    size = property(get_size)


def ext(path):
    ext = os.path.splitext(path)[1]
    return ext.lstrip('.')

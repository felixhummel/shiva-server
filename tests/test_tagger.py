import os
import pytest


@pytest.fixture
def working_files_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'working_files'))


@pytest.fixture
def working_mp3_path(working_files_dir):
    return os.path.join(working_files_dir, 'testfile.mp3')


@pytest.fixture
def working_ogg_path(working_files_dir):
    return os.path.join(working_files_dir, 'testfile.ogg')


def test_TaggedFile(working_mp3_path, working_ogg_path):
    from shiva.tagger import TaggedFile

    tf = TaggedFile(working_mp3_path)
    assert tf.album is not None
    assert tf.artist is not None
    assert tf.title is not None
    assert tf.has_essential_tags

    tf = TaggedFile(working_ogg_path)
    assert tf.album is not None
    assert tf.artist is not None
    assert tf.title is not None
    assert tf.has_essential_tags


def test_TaggedFileList(working_files_dir):
    from shiva.tagger import TaggedFiles
    tfs = TaggedFiles(working_files_dir)
    for tf in tfs.itervalues():
        assert tf.has_essential_tags

def test_ext():
    from shiva.utils import ext
    assert ext('foo.bar') == 'bar'
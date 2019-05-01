import objectbox.version


def test_version():
    info = objectbox.version.version_info()
    assert len(info) > 10

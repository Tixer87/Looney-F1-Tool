from core.version import __version__, FILE_VERSION, PRODUCT_NAME, COMPANY_NAME

def test_version_values():
    assert __version__ == "1.7.2_beta"
    assert FILE_VERSION == (1, 7, 2, 0)
    assert PRODUCT_NAME == "Looney F1 Tool"
    assert COMPANY_NAME == "GridSync"

def test_version_format():
    """Version sollte semantic versioning ähnlich sein"""
    parts = __version__.replace("_", ".").split(".")
    assert len(parts) >= 3  # major.minor.patch (+ optional suffix)
    assert parts[0].isdigit()
    assert parts[1].isdigit()
    assert parts[2].isdigit()

def test_file_version_tuple():
    """FILE_VERSION muss 4-Tupel sein für Windows"""
    assert len(FILE_VERSION) == 4
    assert all(isinstance(x, int) for x in FILE_VERSION)

from core.version import __version__,FILE_VERSION,PRODUCT_NAME,COMPANY_NAME
def test_version_values():
    assert __version__=="1.9.1"
    assert FILE_VERSION==(1,9,1,0)
    assert PRODUCT_NAME=="Looney F1 Tool"
    assert COMPANY_NAME=="GridSync"
def test_file_version_format():
    assert len(FILE_VERSION)==4
    assert all(isinstance(value,int) and value>=0 for value in FILE_VERSION)
def test_version_consistency():
    assert __version__==".".join(map(str,FILE_VERSION[:3]))
    assert FILE_VERSION[3]==0
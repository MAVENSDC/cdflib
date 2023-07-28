import pytest

from cdflib import CDF


def test_read(cdf_path):
    cdf = CDF(cdf_path)

    info = cdf.cdf_info()

    # Smoke test variable access
    for var in info.zVariables:
        cdf.varattsget(var)
        cdf.varget(var)

    # Smoke test context manager
    with CDF(cdf_path) as cdf:
        cdf.cdf_info()

    # Smoke test global attributes
    globalatts = cdf.globalattsget()
    for att in globalatts:
        if len(globalatts[att]) > 1:
            # Make sure multiple entries are unique
            assert len(globalatts[att]) == len(set(globalatts[att]))


def test_nonexist_file_errors(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        CDF(tmp_path / "nonexist.cdf")

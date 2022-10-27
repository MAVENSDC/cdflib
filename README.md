[![Actions Status](https://github.com/MAVENSDC/cdflib/workflows/ci/badge.svg)](https://github.com/MAVENSDC/cdflib/actions)
[![codecov](https://codecov.io/gh/MAVENSDC/cdflib/branch/master/graph/badge.svg?token=IJ6moGc40e)](https://codecov.io/gh/MAVENSDC/cdflib)
[![DOI](https://zenodo.org/badge/102912691.svg)](https://zenodo.org/badge/latestdoi/102912691)
[![Documentation Status](https://readthedocs.org/projects/cdflib/badge/?version=latest)](https://cdflib.readthedocs.io/en/latest/?badge=latest)

# CDFlib

`cdflib` is a python module to read/write CDF (Common Data Format `.cdf`) files without needing to install the
[CDF NASA library](https://cdf.gsfc.nasa.gov/).

Python &ge; 3.6 is required.
This module uses only Numpy, no complicated prereqs.

## Install

To install, open up your terminal/command prompt, and type:
```sh
pip install cdflib
```
There are two different CDF classes: a cdf reader, and a cdf writer.

Currently, you cannot simultaneously read and write to the same file.
Future implementations, however, will unify these two classes.

## Documentation

The full documentation can be found here:

[https://cdflib.readthedocs.io/en/latest/](https://cdflib.readthedocs.io/en/latest/)

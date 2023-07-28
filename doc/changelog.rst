=========
Changelog
=========

1.1.0
=====
- If the `deflate <https://github.com/dcwatson/deflate>`_ library is installed
  it is now used to decompress data, which can lead to around 2x speedups over
  the native gzip Python library.
- Fixed reading attributes with multiple entries when using `cdflib.cdfread.CDF.globalattsget`.

1.0.5
=====
- Fixed the output of :meth:`cdflib.epochs.CDFepoch.compute_tt2000` to
  be squeezed if a single input is given.
- Fixed warnings with numpy 1.25.

1.0.4
=====
- Fixed issue where multi-dimensional variables were dropped when converting to xarray.
- Replaced all print and warning statements with a logger, ``cdflib.logging.logger``.

1.0.3
=====
- The ``variable`` parameter to `cdflib.cdfread.CDF.varattsget` is no longer optional.
  Not specifying it raised an error anyway in previous versions of cdflib.
- Fixed an error loading CDF files without a pad value set.

1.0.2
=====
To make the ``xarray`` functionality easier to discover and import, a new
``cdflib.xarray`` namespace has been added. This means the recommended
way to import the xarray functionality is now
``from cdflib.xarray import cdf_to_xarray, xarray_to_cdf``


1.0.1
=====
To keep ``astropy`` and ``xarray`` as optional dependencies, ``cdfastropy``,
``cdf_to_xarray``, and ``xarray_to_cdf`` are no longer available under ``cdflib``.
Instead import them from
``cdflib.xarray_to_cdf.xarray_to_cdf``,
``cdflib.cdf_to_xarray.cdf_to_xarray``, or
``cdflib.epochs_astropy.CDFAstropy``.

1.0.0
=====
Version 1.0.0 is a new major version for ``cdflib``, and contains a number
of breaking changes. These have been made to improve consistency across the
package, and make it easier to maintain and build on the package going forward
in the future.

Although we have tried our best to not introduce new bugs and
list all changes below, some things may have slipped through the cracks. If you
have any issues, please do not hesitate to open them at https://github.com/MAVENSDC/cdflib/issues.

Python support
--------------
``cdflib`` is now only tested on Python 3.8, 3.9, 3.10, and 3.11. It may work
for older versions of Python, but this is not guarenteed. If you need to
use ``cdflib`` on an older version of Python, please open an issue to
discuss whether the ``cdflib`` maintainers can support this.

Returning arrays
----------------
All ``to_np`` keyword arguments have been removed throughout the library, and the
code now behaves as if ``to_np=True`` throughout. This change has been made to
reduce code omplexity and make maintaining the code easier. If you need outputs
as lists, call ``.tolist()`` on the output array.

``to_np=True`` was the deafult in ``cdfread``, so if you weren't specifying it
behaviour will not change there. ``to_np=False`` was the default in ``epochs``,
so if you weren't specifying it there beahviour **will** change.

Changes to CDF method returns
-----------------------------
Most of the methods that return data from the CDF reader class have had their
return types changed from dictionaries to dataclasses. This allows the return
type to be more clearly documented (see :ref:`dataclasses`), for internal
checks to be made to make sure data types are consistent, and a nicer
representation when the return values are printed.

Where previously an item would have been accessed as ``dict["value"]``,
items in the dataclasses can be accessed using ``dataclass.value``.

The methods that have been updated are:

- `cdflib.cdfread.CDF.vdr_info`
- `cdflib.cdfread.CDF.attinq`
- `cdflib.cdfread.CDF.attget`
- `cdflib.cdfread.CDF.varget`
- `cdflib.cdfread.CDF.varinq`

Other breaking changes
----------------------
- The CDF factory class (``cdflib.CDF``) has been removed, and ``cdflib.CDF``
  is now the reader class. This change has been made to prevent potential
  confusion when the user makes a mistake in specifying the file to open,
  and ``cdflib`` would silently create a writer class instead. If you want
  to create a CDF writer class, explicitly import `cdflib.cdfwrite.CDF`
  instead.
- `cdflib.cdfread.CDF.varget` no longer takes an ``inq`` argument. Instead
  use the new method `cdflib.cdfread.CDF.vdr_info` to get the VDR info.
- ``getVersion()`` methods have been removed throughout the package. Instead
  the CDF version can be read from class attributes.
- Removed ``cdflib.cdfepochs.CDFepoch.getLeapSecondLastUpdated``.
  Directly inspect `CDFepoch.LTS` instead to get the last date at which a
  leapsecond was added.
- The ``expand`` keyword argument to `cdflib.cdfread.CDF.varget` has been removed.
  Use ``CDF.varinq`` to get variable information instead.
- The ``expand`` keyword argument to ``CDF.globalattsget`` and ``CDF.varattsget`` has been removed.
  Use `cdflib.cdfread.CDF.attinq` to get attribute information instead.
- Removed ``CDF.print_attrs``
- The ``version``, ``release``, and ``increement`` attributes of ``CDF`` have been removed.
- Removed the ``record_range_only`` argument to `cdflib.cdfread.CDF.varget`.
- Removed ``CDF.epochrange``. Use `cdflib.cdfread.CDF.varinq` instead to get the data ranges.

New features
------------
- Type hints have been added across the majority of the package.

Bugfixes
--------
- ``"Majority"`` is now correctly read from the CDF spec if present.

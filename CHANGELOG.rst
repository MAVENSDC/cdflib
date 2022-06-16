cdflib 1.0.0
============

Python support
--------------
``cdflib`` is now only tested on Python 3.8, 3.9, and 3.10. It may work
for older versions of Python, but this is not guarenteed. If you need to
use ``cdflib`` on an older version of Python, please open an issue to
discuss whether the ``cdflib`` maintainers can support this.

Breaking changes
----------------
- The CDF factory class (``cdflib.CDF``) has been removed, and `cdflib.CDF`
  is now the reader class. This change has been made to prevent potential
  confusion when the user makes a mistake in specifying the file to open,
  and ``cdflib`` would silently create a writer class instead. If you want
  to create a CDF writer class, explicitly import `cdflib.cdfwrite.CDF`
  instead.

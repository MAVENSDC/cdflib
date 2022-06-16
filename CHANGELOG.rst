cdflib 1.0.0
============

Breaking changes
----------------
- The CDF factory class (``cdflib.CDF``) has been removed, and `cdflib.CDF`
  is now the reader class. This change has been made to prevent potential
  confusion when the user makes a mistake in specifying the file to open,
  and ``cdflib`` would silently create a writer class instead. If you want
  to create a CDF writer class, explicitly import `cdflib.cdfwrite.CDF`
  instead.

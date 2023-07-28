try:
    from deflate import gzip_decompress as gzip_inflate
    from deflate import gzip_compress as gzip_deflate

except ImportError:
    from gzip import decompress as gzip_inflate
    from gzip import compress as gzip_deflate

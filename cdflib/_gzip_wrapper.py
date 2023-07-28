try:
    from deflate import gzip_compress as gzip_deflate
    from deflate import gzip_decompress as gzip_inflate

except ImportError:
    from gzip import compress as gzip_deflate
    from gzip import decompress as gzip_inflate


__all__ = ["gzip_inflate", "gzip_deflate"]

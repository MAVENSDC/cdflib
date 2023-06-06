import io


class S3object:
    """
    Handler for S3 objects so they behave like files.
    S3 'read' reads specified byte range
    S3 'seek' sets byte range for subsequent readers
    """

    def __init__(self, fhandle):
        self.pos = 0  # used to track where in S3 we are
        self.content_length = fhandle.content_length  # size in bytes
        self.fhandle = fhandle
        self.temp_file = None

    def read(self, isize):
        if isize == -1:
            isize = self.content_length
        myrange = "bytes=%d-%d" % (self.pos, (self.pos + isize - 1))
        self.pos += isize  # advance the pointer
        stream = self.fhandle.get(Range=myrange)["Body"]
        rawdata = stream.read()
        # bdata=io.BytesIO(rawdata)
        return rawdata

    def seek(self, offset, from_what=0):
        if from_what == 2:
            # offset is from end of file, ugh, used only for checksum
            self.pos = self.content_length + offset
        elif from_what == 1:
            # from current position
            self.pos = self.pos + offset
        else:
            # usual default is 0, from start of file
            self.pos = offset

    def tell(self):
        return self.pos

    def fetchS3entire(self):
        obj = self.fhandle.get()["Body"]
        rawdata = obj["Body"].read()
        bdata = io.BytesIO(rawdata)
        return bdata

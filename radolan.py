#
# Under construction....
#
class RadolanFile:

    header_length = 88

    @staticmethod
    def readHeader(stream):
        headerBytes = bytearray(RadolanFile.header_length)
        assert stream.readinto(headerBytes) == RadolanFile.header_length, 'file too short'
        print(stream)
        assert headerBytes[41:43] == b'PR', 'PR in header is missing -> wrong file format'
        assert headerBytes[55:57] == b'GP', 'GP in header is missing -> wrong file format'
        assert headerBytes[83:85] == b'MS', 'MS in header is missing -> wrong file format'
        msLen = int(headerBytes[85:88])
        assert msLen <= 999, 'MS string too long -> wrong file format'
        stream.read(msLen) # ignore the MS data
        assert stream.read(1) == b'\x03' ,'\\x03 at the end of header is missing -> wrong file format'
        product = headerBytes[0:2]
        print(product)
        DDhhmm = headerBytes[2:8]
        print(DDhhmm)
        MMYY = headerBytes[13:17]
        print(MMYY)
        timestamp = RadolanFile.__convertToTimestamp(DDhhmm.decode(), MMYY.decode())
        print(timestamp)
        precisionStr = headerBytes[44:48]
        print(precisionStr)
        precision = RadolanFile.__decodePrecision(precisionStr.decode())
        print(precision)
        dimension = headerBytes[57:66]
        print(dimension)
        return {
            'product' : product.decode(),
            'timestamp' : timestamp,
            'precision' : precision,
            'dimension' : dimension.decode()
        }

    @staticmethod
    def __convertToTimestamp(DDhhmm, MMYY):
        # '2022-06-13T12:00:00.000Z
        return '20' + MMYY[2:4]+ '-' + MMYY[0:2] + '-' + DDhhmm[0:2] + 'T' +\
            DDhhmm[2:4] + ':' + DDhhmm[4:6] + ':00.000Z'

    @staticmethod
    def __decodePrecision(precision):
        return pow(10, int(precision[1:4]))


if __name__ == "__main__":
    stream = open("DE1200_RV2202131540_000", "rb")
    print(RadolanFile.readHeader(stream))

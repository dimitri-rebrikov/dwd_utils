#
# Under construction....
#
import math
import tarfile
from urllib.request import urlopen
class RadolanFile:

    header_length = 88

    @staticmethod
    def readHeader(stream):
        headerBytes = stream.read(RadolanFile.header_length)
        assert  len(headerBytes) == RadolanFile.header_length, 'file too short'
        # print(headerBytes)
        assert headerBytes[41:43] == b'PR', 'PR in header is missing -> wrong file format'
        assert headerBytes[55:57] == b'GP', 'GP in header is missing -> wrong file format'
        assert headerBytes[66:68] == b'VV', 'VV in header is missing -> wrong file format'
        assert headerBytes[83:85] == b'MS', 'MS in header is missing -> wrong file format'
        msLen = int(headerBytes[85:88])
        assert msLen <= 999, 'MS string too long -> wrong file format'
        stream.read(msLen) # ignore the MS data
        assert stream.read(1) == b'\x03' ,'\\x03 at the end of header is missing -> wrong file format'
        product = headerBytes[0:2]
        # print(product)
        DDhhmm = headerBytes[2:8]
        # print(DDhhmm)
        MMYY = headerBytes[13:17]
        # print(MMYY)
        timestamp = RadolanFile.__convertToTimestamp(DDhhmm.decode(), MMYY.decode())
        # print(timestamp)
        precisionStr = headerBytes[44:48]
        # print(precisionStr)
        precision = RadolanFile.__decodePrecision(precisionStr.decode())
        # print(precision)
        dimension = headerBytes[57:66]
        # print(dimension)
        [size_y, size_x] = map(lambda val: int(val), dimension.split(b'x', 2))
        # print(size_x, size_y)
        forecast = headerBytes[69:72]
        return {
            'product' : product.decode(),
            'timestamp' : timestamp,
            'precision' : precision,
            'dimension' : { 'x': size_x, 'y': size_y},
            'forecast' : forecast.decode()
        }

    @staticmethod
    def __convertToTimestamp(DDhhmm, MMYY):
        # '2022-06-13T12:00:00.000Z
        return '20' + MMYY[2:4]+ '-' + MMYY[0:2] + '-' + DDhhmm[0:2] + 'T' +\
            DDhhmm[2:4] + ':' + DDhhmm[4:6] + ':00.000Z'

    @staticmethod
    def __decodePrecision(precision):
        return pow(10, int(precision[1:4]))

    @staticmethod
    def readSingleValue(header, stream, x, y):
        header_x = header['dimension']['x']
        header_y = header['dimension']['y']
        assert x < header_x, "x shall be lesser than " + str(header_x)
        assert y < header_y, "y shall be lesser than " + str(header_y)
        dataRow = bytearray(header_x * 2)
        for rowNr in range(y + 1):
            assert stream.readinto(dataRow) == len(dataRow), 'file too short'
            # print(dataRow, '\n')
        valBytes = dataRow[x * 2 : x * 2 + 2]
        # print(valBytes)
        if valBytes == b'\xc4\x29':
            return -1
        return float(int.from_bytes(valBytes, 'little')) * header['precision']

class RadolanMatrix:

    matrix_definitions = {
        (1200, 1100): {'dy':600 , 'dx':470},
        (900, 900): {'dy':450 , 'dx':450},
    }

    @staticmethod
    def getMatrixCoord(matrixDimensionYX, lat, lon):
        matrix_definition = RadolanMatrix.matrix_definitions[matrixDimensionYX]
        assert matrix_definition, 'unknown matrix dimension: ' + matrixDimensionYX
        #print(matrix_definition)
        [x_0, y_0] = RadolanMatrix.getRadolanCoord(51, 9)
        #print(x_0, y_0)
        x_0 = x_0 - matrix_definition['dx']
        y_0 = y_0 - matrix_definition['dy']
        #print(x_0, y_0)
        [x, y] = RadolanMatrix.getRadolanCoord(lat, lon)
        #print(x, y)
        x = x - x_0
        y = y - y_0
        #print(x, y)
        assert x < matrixDimensionYX[1] and y < matrixDimensionYX[0], "provided lan/lot are outside of the matrix"
        return [math.ceil(x), math.ceil(y)]

    @staticmethod
    def getRadolanCoord(lat, lon):
        phi_0 = math.radians(60)
        phi_m = math.radians(lat)
        lam_0 = 10
        lam_m = lon
        lam = math.radians(lam_m - lam_0)
        er = 6370.040
        m_phi = (1 + math.sin(phi_0)) / (1 + math.sin(phi_m))
        x = er * m_phi * math.cos(phi_m) * math.sin(lam)
        y = -er * m_phi * math.cos(phi_m) * math.cos(lam)
        return [x, y]

class RadolanBzipFile:

    @staticmethod
    def getFileStreams(bzStream):
        tf = tarfile.open(fileobj=bzStream, mode="r|bz2")
        for tarInfo in tf:
            if tarInfo.isfile():
                # print("yeld", tarInfo.name)
                yield [tarInfo.name, tf.extractfile(tarInfo) ]

class RadolanProducts:

    @staticmethod
    def getLatestRvData(lat, lon):
        bzStream = urlopen("https://opendata.dwd.de/weather/radar/composit/rv/DE1200_RV_LATEST.tar.bz2")
        timestamp = ''
        forecasts = []
        for fileName, fileStream in RadolanBzipFile.getFileStreams(bzStream):
            # print(fileName)
            header = RadolanFile.readHeader(fileStream)
            if not timestamp:
                timestamp = header['timestamp']
            # print(header)
            dimension = ( header['dimension']['y'] , header['dimension']['x'] )
            # print(dimension)
            [x, y] = RadolanMatrix.getMatrixCoord(dimension, lat, lon)
            # print(x, y)
            value = RadolanFile.readSingleValue(header, fileStream, x, y)
            # print(value)
            value = value * 12 # to get liter per hour 
            value = float("{:.2f}".format(value)) # shorten to 2 decimal numbers
            forecasts.append({'forecast' : header['forecast'], 'value' : value})
            fileStream.close()
        bzStream.close()
        return { 'timestamp' : timestamp, 'forecasts' : forecasts }

if __name__ == "__main__":
    #
    # usage examples
    #
    print(RadolanProducts.getLatestRvData(49.168089159811565, 10.153924630472927))


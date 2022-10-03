#
# Under construction....
#
from math import sin, cos, radians, ceil
import tarfile
from urllib.request import urlopen, Request
from urllib.error import HTTPError
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
    def readValues(header, stream, xYTupleSet):
        header_x = header['dimension']['x']
        header_y = header['dimension']['y']
        for x, y in xYTupleSet:
            assert x < header_x, "x (" + str(x) + ") shall be lesser than " + str(header_x)
            assert y < header_y, "y (" + str(y)  + ") shall be lesser than " + str(header_y)
        dataRow = bytearray(header_x * 2)
        result = {}
        for curY in range(header_y):
            assert stream.readinto(dataRow) == len(dataRow), 'file too short'
            # print(dataRow, '\n')
            for curX in range(header_x):
                if((curX, curY) in xYTupleSet):
                    valBytes = dataRow[curX * 2 : curX * 2 + 2]
                    # print(valBytes)
                    if valBytes == b'\xc4\x29':
                        value = -1
                    else:
                        value= float(int.from_bytes(valBytes, 'little')) * header['precision']
                    result[(curX, curY)] = value
        return result
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
    def getCompositeBaseUrl():
        newUrl = 'https://opendata.dwd.de/weather/radar/composite'
        oldUrl = 'https://opendata.dwd.de/weather/radar/composit'
        try:
            urlopen(newUrl)
            return newUrl
        except HTTPError:
            return oldUrl

    @staticmethod
    def __getLatestRvDataFileUrl():
        return RadolanProducts.getCompositeBaseUrl()+'/rv/DE1200_RV_LATEST.tar.bz2'

    @staticmethod
    def getLatestRvDataTimestamp():
        return RadolanProducts.getRadolanDataTimestamp(RadolanProducts.__getLatestRvDataFileUrl())

    @staticmethod
    def getLatestRvData(latLonTupleSet):
        def valueLambda(value):
            if value > 0:
                value = value * 12 # to get liter per hour as stated in the RV documentation
                value = float("{:.2f}".format(value)) # shorten to 2 decimal numbers
            return value

        return RadolanProducts.getRadolanForecastData(RadolanProducts.__getLatestRvDataFileUrl(), latLonTupleSet, valueLambda)

    @staticmethod
    def getRadolanForecastData(bz2FileUrl, xyTupleSet, valueLambda=None):
        bzStream = urlopen(bz2FileUrl)
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
            values = RadolanFile.readValues(header, fileStream, xyTupleSet)
            # print(values)
            forecasts.append({'forecast' : header['forecast'], 'values' : values})
            fileStream.close()
        bzStream.close()
        return { 'timestamp' : timestamp, 'forecasts' : forecasts }

    @staticmethod
    def getRadolanDataTimestamp(fileUrl):
        return urlopen(Request(url=fileUrl, method='HEAD')).getheader('last-modified')


if __name__ == "__main__":
    #
    # usage examples
    #

    # get timestamp of the data
    print(RadolanProducts.getLatestRvDataTimestamp())
    # get current RV (rain amount) data
    from poi2RadolanRvMap import poi2RadolanRvMap
    print(RadolanProducts.getLatestRvData({poi2RadolanRvMap['70567']}))

    # get data from specific DWD file
    print(RadolanProducts.getRadolanForecastData('https://opendata.dwd.de/weather/radar/composit/rv/DE1200_RV_LATEST.tar.bz2', {(882, 606),(860, 714)}))
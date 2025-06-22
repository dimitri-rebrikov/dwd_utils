from math import sin, cos, radians, ceil
import tarfile
from urllib.request import urlopen, Request
from urllib.error import HTTPError
class RadolanFile:

    header_length = 91

    @staticmethod
    def readHeader(stream):
        headerBytes = stream.read(RadolanFile.header_length)
        assert  len(headerBytes) == RadolanFile.header_length, 'file too short'
        #print(headerBytes)
        assert headerBytes[44:46] == b'PR', 'PR in header is missing -> wrong file format'
        assert headerBytes[58:60] == b'GP', 'GP in header is missing -> wrong file format'
        assert headerBytes[69:71] == b'VV', 'VV in header is missing -> wrong file format'
        assert headerBytes[86:88] == b'MS', 'MS in header is missing -> wrong file format'
        msLen = int(headerBytes[88:91])
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
        precisionStr = headerBytes[47:51]
        # print(precisionStr)
        precision = RadolanFile.__decodePrecision(precisionStr.decode())
        # print(precision)
        dimension = headerBytes[60:69]
        # print(dimension)
        [size_y, size_x] = map(lambda val: int(val), dimension.split(b'x', 2))
        # print(size_x, size_y)
        forecast = headerBytes[72:75]
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
    def readValues(header, stream, xyxyTupleSet, callback):
        header_x = header['dimension']['x']
        header_y = header['dimension']['y']
        for x0, y0, x1, y1 in xyxyTupleSet:
            assert x0 < header_x, "x0 (" + str(x0) + ") shall be lesser than " + str(header_x)
            assert y0 < header_y, "y0 (" + str(y0)  + ") shall be lesser than " + str(header_y)
            assert x1 < header_x, "x1 (" + str(x1) + ") shall be lesser than " + str(header_x)
            assert y1 < header_y, "y1 (" + str(y1)  + ") shall be lesser than " + str(header_y)
        dataRow = bytearray(header_x * 2)
        for curY in range(header_y):
            assert stream.readinto(dataRow) == len(dataRow), 'file too short'
            # print(dataRow, '\n')
            for curX in range(header_x):
                for x0, y0, x1, y1 in xyxyTupleSet:
                    if curX >= x0 and curY >= y0 and curX <= x1 and curY <= y1:
                        valBytes = dataRow[curX * 2 : curX * 2 + 2]
                        # print(valBytes)
                        if valBytes == b'\xc4\x29':
                            value = -1
                        else:
                            value= float(int.from_bytes(valBytes, 'little')) * header['precision']
                        callback((curX, curY), value)

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
        return 'https://opendata.dwd.de/weather/radar/composite'

    @staticmethod
    def __getLatestRvDataFileUrl():
        return RadolanProducts.getCompositeBaseUrl()+'/rv/DE1200_RV_LATEST.tar.bz2'

    @staticmethod
    def getLatestRvDataTimestamp():
        return RadolanProducts.getRadolanDataTimestamp(RadolanProducts.__getLatestRvDataFileUrl())

    @staticmethod
    def getLatestRvData(xyxyTupleSet):
        return RadolanProducts.getRvData(RadolanProducts.__getLatestRvDataFileUrl(), xyxyTupleSet)

    @staticmethod
    def getRvData(bz2RvFileUrl, xyxyTupleSet):
        def valueLambda(value):
            if value > 0:
                value = value * 12 # to get liter per hour as stated in the RV documentation
                value = float("{:.2f}".format(value)) # shorten to 2 decimal numbers
            return value
        return RadolanProducts.getRadolanForecastData(bz2RvFileUrl, xyxyTupleSet, valueLambda)

    @staticmethod
    def getRadolanForecastData(bz2FileUrl, xyxyTupleSet, valueLambda=None):
        timestamp = None
        curHeader = None
        forecasts = []
        values = None
        def nextFileCallback(header):
            nonlocal timestamp
            if header != None:
                timestamp = header['timestamp']
            nonlocal curHeader, values
            if curHeader != None:
                forecasts.append({'forecast' : curHeader['forecast'], 'values' : values})
            curHeader = header
            values = {} 
        def valuesCallback(xyTuple, value):
            nonlocal values
            values[xyTuple] = value
        RadolanProducts.parseRadolanForecastData(bz2FileUrl, xyxyTupleSet, nextFileCallback, valuesCallback, valueLambda)
        return { 'timestamp' : timestamp, 'forecasts' : forecasts }

    @staticmethod
    def parseRadolanForecastData(bz2FileUrl, xyxyTupleSet, nextFileCallback, valuesCallback, valueLambda=None):
        bzStream = urlopen(bz2FileUrl)
        for fileName, fileStream in RadolanBzipFile.getFileStreams(bzStream):
            # print(fileName)
            header = RadolanFile.readHeader(fileStream)
            # print(header)
            nextFileCallback(header)
            def intValuesCallback(xyTuple, value):
                nonlocal valueLambda, valuesCallback
                if valueLambda != None:
                    value = valueLambda(value)
                valuesCallback(xyTuple, value)
            RadolanFile.readValues(header, fileStream, xyxyTupleSet, intValuesCallback)
            fileStream.close()
        bzStream.close()
        nextFileCallback(None)
        
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
    xy = poi2RadolanRvMap['70567']
    xyxy = (xy[0],xy[1],xy[0],xy[1])
    print(RadolanProducts.getLatestRvData({xyxy}))

    # get data from specific DWD file
    # print(RadolanProducts.getRadolanForecastData('https://opendata.dwd.de/weather/radar/composit/rv/DE1200_RV_LATEST.tar.bz2', {(882, 606, 882, 606),(860, 714, 860, 714)}))
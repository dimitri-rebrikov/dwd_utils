
from math import sin, cos, radians, ceil
import tarfile
import h5py
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from datetime import datetime
import io

class RadolanHdf5File:

    @staticmethod
    def __convertToTime(YYMMDD, HHMMSS):
        # '2022-06-13T12:00:00.000Z
        return datetime.strptime(YYMMDD+HHMMSS, '%Y%m%d%H%M%S')

    @staticmethod
    def readInfo(h5):
        endtime = RadolanHdf5File.__convertToTime(h5['dataset1']['what'].attrs['enddate'].decode(),
                                                            h5['dataset1']['what'].attrs['endtime'].decode())
        timestamp = RadolanHdf5File.__convertToTime(h5['what'].attrs['date'].decode(),
                                                            h5['what'].attrs['time'].decode())
        return {
                'product' : h5['how']['POLARA'].attrs['pattern'].decode(),
                'timestamp' : timestamp,
                'gain' : h5['dataset1']['data1']['what'].attrs['gain'],
                'nodata' : h5['dataset1']['data1']['what'].attrs['nodata'],
                'offset' : h5['dataset1']['data1']['what'].attrs['offset'],
                'xsize' : h5['where'].attrs['xsize'], 
                'ysize' : h5['where'].attrs['ysize'],
                'forecast' : int((endtime - timestamp).total_seconds() / 60.0)
            }
        
    @staticmethod
    def readValues(info, dataSet, xyxyTupleSet, callback):
        for x0, y0, x1, y1 in xyxyTupleSet:
            assert x0 < info['xsize'], "x0 (" + str(x1) + ") shall be lesser than " + str(info['xsize'])
            assert y0 < info['ysize'], "y0 (" + str(y1)  + ") shall be lesser than " + str(info['ysize'])
            assert x1 < info['xsize'], "x1 (" + str(x1) + ") shall be lesser than " + str(info['xsize'])
            assert y1 < info['ysize'], "y1 (" + str(y1)  + ") shall be lesser than " + str(info['ysize'])
        data = dataSet[()]
        for xyxyTuple in xyxyTupleSet:
            for y in range(xyxyTuple[1], xyxyTuple[3]+1):
                for x in range(xyxyTuple[0], xyxyTuple[2]+1):
                    value = data[y, x]
                    value = value.item()
                    # print(value)
                    if value == info['nodata']:
                        value = -1
                    else:
                        value = round(value * info['gain'] + info['offset'], 2)
                    # print(value)
                    callback((x, y), value)
                    x = x + 1
                    y = y + 1 

class RadolanHdf5Products:

    @staticmethod 
    def getCompositeBaseUrl():
        return 'https://opendata.dwd.de/weather/radar/composite'

    @staticmethod
    def __getLatestRvDataFileUrl():
        return RadolanHdf5Products.getCompositeBaseUrl()+'/rv/composite_rv_LATEST.tar'

    @staticmethod
    def getLatestRvDataTimestamp():
        return RadolanHdf5Products.getRadolanDataTimestamp(RadolanHdf5Products.__getLatestRvDataFileUrl())

    @staticmethod
    def getLatestRvData(xyTupleSet):
        return RadolanHdf5Products.getRvData(RadolanHdf5Products.__getLatestRvDataFileUrl(), xyTupleSet)

    @staticmethod
    def getRvData(h5TarFileUrl, xyTupleSet):
        def valueLambda(value):
            if value > 0:
                value = value * 12 # to get liter per hour as stated in the RV documentation
                value = float("{:.2f}".format(value)) # shorten to 2 decimal numbers
            return value
        return RadolanHdf5Products.getRadolanForecastData(h5TarFileUrl, xyTupleSet, valueLambda)
    
    @staticmethod
    def getRadolanForecastData(h5TarFileUrl, xyxyTupleSet, valueLambda=None):
        timestamp = None
        curInfo = None
        forecasts = []
        values = None
        def nextFileCallback(info):
            nonlocal timestamp
            if info != None:
                timestamp = info['timestamp']
            nonlocal curInfo, values
            if curInfo != None:
                forecasts.append({'forecast' : curInfo['forecast'], 'values' : values})
            curInfo = info
            values = {} 
        def valuesCallback(xyTuple, value):
            nonlocal values
            values[xyTuple] = value
        RadolanHdf5Products.parseRadolanForecastData(h5TarFileUrl, xyxyTupleSet, nextFileCallback, valuesCallback, valueLambda)
        return { 'timestamp' : RadolanHdf5Products.__convertToString(timestamp), 'forecasts' : forecasts }
    
    @staticmethod
    def parseRadolanForecastData(h5TarFileUrl, xyxyTupleSet, nextFileCallback, valuesCallback, valueLambda=None):
        tarStream = urlopen(h5TarFileUrl)
        timestamp = ''
        forecasts = []
        tf = tarfile.open(fileobj=tarStream, mode='r|')
        for fileInfo in tf:
            # print(fileInfo)
            h5mem = io.BytesIO(tf.extractfile(fileInfo).read())
            h5 = h5py.File(h5mem, 'r')
            info = RadolanHdf5File.readInfo(h5)
            nextFileCallback(info)
            def intValuesCallback(xyTuple, value):
                nonlocal valueLambda, valuesCallback
                if valueLambda != None:
                    value = valueLambda(value)
                valuesCallback(xyTuple, value)
            RadolanHdf5File.readValues(info, h5['dataset1']['data1']['data'], xyxyTupleSet, intValuesCallback)
            h5.close()
        tarStream.close()
        nextFileCallback(None)

    @staticmethod
    def getRadolanDataTimestamp(fileUrl):
        return urlopen(Request(url=fileUrl, method='HEAD')).getheader('last-modified')
    
    @staticmethod
    def __convertToString(datetime):
        return datetime.strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    #
    # usage examples
    #

    # get timestamp of the data
    print(RadolanHdf5Products.getLatestRvDataTimestamp())
    # get current RV (rain amount) data
    from poi2RadolanHdf5RvMap import poi2RadolanHdf5RvMap
    xy = poi2RadolanHdf5RvMap['70567']
    xyxy = (xy[0],xy[1],xy[0],xy[1])
    print(RadolanHdf5Products.getLatestRvData({xyxy}))

    # get data from specific DWD file
    # print(RadolanProducts.getRadolanForecastData('https://opendata.dwd.de/weather/radar/composit/rv/DE1200_RV_LATEST.tar.bz2', {(882, 606, 882, 606),(860, 714, 860, 714)}))
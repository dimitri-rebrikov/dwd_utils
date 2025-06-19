
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
                'forecast' : (endtime - timestamp).total_seconds() / 60.0
            }
        
    @staticmethod
    def readValues(info, dataSet, xYTupleSet):
        for x, y in xYTupleSet:
            assert x < info['xsize'], "x (" + str(x) + ") shall be lesser than " + str(info['xsize'])
            assert y < info['ysize'], "y (" + str(y)  + ") shall be lesser than " + str(info['ysize'])
        result = {}
        for xYTuple in xYTupleSet:
            value = dataSet[xYTuple[1], xYTuple[0]]
            # print(value)
            if value == info['nodata']:
                value = -1
            else:
                value= value * info['gain'] + info['offset']
            # print(value)
            result[(xYTuple[0], xYTuple[1])] = value.item()
        return result

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
    def getRadolanForecastData(h5TarFileUrl, xyTupleSet, valueLambda=None):
        tarStream = urlopen(h5TarFileUrl)
        timestamp = ''
        forecasts = []
        tf = tarfile.open(fileobj=tarStream, mode='r|')
        for fileInfo in tf:
            # print(fileInfo)
            h5mem = io.BytesIO(tf.extractfile(fileInfo).read())
            h5 = h5py.File(h5mem, 'r')
            info = RadolanHdf5File.readInfo(h5)
            if not timestamp:
                timestamp = info['timestamp']
            # print(header)
            values = RadolanHdf5File.readValues(info, h5['dataset1']['data1']['data'], xyTupleSet)
            # print(values)
            result = {}
            if valueLambda != None:
                for key in values:
                    values[key] = valueLambda(values[key])
                # print("after lambda", values)
            forecasts.append({'forecast' : '{:03.0f}'.format(info['forecast']), 'values' : values})
            h5.close()
        tarStream.close()
        return { 'timestamp' : RadolanHdf5Products.__convertToString(timestamp), 'forecasts' : forecasts }

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
    print(RadolanHdf5Products.getLatestRvData({poi2RadolanRvMap['70567']}))

    # get data from specific DWD file
    # print(RadolanProducts.getRadolanForecastData('https://opendata.dwd.de/weather/radar/composit/rv/DE1200_RV_LATEST.tar.bz2', {(882, 606),(860, 714)}))
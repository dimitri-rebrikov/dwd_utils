from radolan_hdf5 import RadolanHdf5Products
import numpy
image = None
curHeader = None
values = None
maxValue = 0
def nextFileCallback(header):
    global image, curHeader, values
    if curHeader != None:
        size=(curHeader['xsize'], curHeader['ysize'])
        array = numpy.empty(size)
        for xy in values.keys():
            array[xy[0], xy[1]] = values[xy]
        numpy.savetxt(curHeader['product'] + str(curHeader['forecast']) + '_hdf5.csv', array, fmt='%3.2f', delimiter=';')
    curHeader = header
    values = {} 
def valuesCallback(xyTuple, value):
    global values, maxValue
    values[xyTuple] = value
    if value > maxValue:
        maxValue = value
RadolanHdf5Products.parseRadolanForecastData('file:./testdata/composite_rv_20250615_1820.tar', {(0,0,1099,1199)}, nextFileCallback, valuesCallback)
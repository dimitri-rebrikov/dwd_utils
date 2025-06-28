from radolan import RadolanProducts
import numpy
array = None
curHeader = None
values = None
maxValue = 0
def nextFileCallback(header):
    global image, curHeader, values
    if curHeader != None:
        size=(curHeader['dimension']['y'], curHeader['dimension']['x'])
        array = numpy.empty(size)
        for xy in values.keys():
            array[size[1]-1-xy[1], xy[0]] = values[xy]
        numpy.savetxt(curHeader['product'] + str(curHeader['forecast']) + '.csv', array, fmt='%3.2f', delimiter=';')
    curHeader = header
    values = {} 
def valuesCallback(xyTuple, value):
    global values, maxValue
    values[xyTuple] = value
    if value > maxValue:
        maxValue = value
RadolanProducts.parseRadolanForecastData('file:./testdata/DE1200_RV2506151820.tar.bz2', {(0,0,1099,1199)}, nextFileCallback, valuesCallback)
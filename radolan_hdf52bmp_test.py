from radolan_hdf5 import RadolanHdf5Products
from PIL import Image
image = None
curHeader = None
values = None
maxValue = 0
def nextFileCallback(header):
    global image, curHeader, values
    if curHeader != None:
        size=(curHeader['xsize'], curHeader['ysize'])
        image = Image.new('RGB', size, '#fff')
        px = image.load()
        for xy in values.keys():
            value = 255 - int(round(values[xy]/maxValue * 255,0))
            px[xy[0], xy[1]] = (value, value, value)
        image.save(curHeader['product'] + str(curHeader['forecast']) + '.jpeg')
        image.close()
    curHeader = header
    values = {} 
def valuesCallback(xyTuple, value):
    global values, maxValue
    values[xyTuple] = value
    if value > maxValue:
        maxValue = value
RadolanHdf5Products.parseRadolanForecastData('file:./testdata/composite_rv_20250615_1820.tar', {(0,0,1099,1199)}, nextFileCallback, valuesCallback)
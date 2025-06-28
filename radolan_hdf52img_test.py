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
            value = values[xy]
            if value == -1:
                color = (0, 0, 0)
            elif value == 0:
                color = (255, 255, 255)
            else: 
                value = 125 - int(round(value/maxValue * 125,0))
                color = (value, value, value)
            px[xy[0], xy[1]] = color
        image.save(curHeader['product'] + str(curHeader['forecast']) + '_hdf5.jpeg')
        image.close()
    curHeader = header
    values = {} 
def valuesCallback(xyTuple, value):
    global values, maxValue
    values[xyTuple] = value
    if value > maxValue:
        maxValue = value
RadolanHdf5Products.parseRadolanForecastData('file:./testdata/composite_rv_20250615_1820.tar', {(0,0,1099,1199)}, nextFileCallback, valuesCallback)
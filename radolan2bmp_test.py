from radolan import RadolanProducts
from PIL import Image
image = None
curHeader = None
values = None
maxValue = 0
def nextFileCallback(header):
    global image, curHeader, values
    if curHeader != None:
        size=(curHeader['dimension']['x'], curHeader['dimension']['y'])
        image = Image.new('RGB', size, '#fff')
        px = image.load()
        for xy in values.keys():
            value = 255 - int(round(values[xy]/maxValue * 255,0))
            px[xy[0], size[1]-1-xy[1]] = (value, value, value)
        image.save(curHeader['product'] + str(curHeader['forecast']) + '.jpeg')
        image.close()
    curHeader = header
    values = {} 
def valuesCallback(xyTuple, value):
    global values, maxValue
    values[xyTuple] = value
    if value > maxValue:
        maxValue = value
RadolanProducts.parseRadolanForecastData('file:./testdata/DE1200_RV2506151820.tar.bz2', {(0,0,1099,1199)}, nextFileCallback, valuesCallback)
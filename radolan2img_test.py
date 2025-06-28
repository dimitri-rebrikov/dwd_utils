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
            value = values[xy]
            if value == -1:
                color = (0, 0, 0)
            elif value == 0:
                color = (255, 255, 255)
            else: 
                value = 125 - int(round(value/maxValue * 125,0))
                color = (value, value, value)
            px[xy[0], size[1]-1-xy[1]] = color
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
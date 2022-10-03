# converts lat, lon coordinates 
# to RADOLAN RV matrix x, y coordinates 
# based on the ball (german "kugel") earth model
# using trigonometric functions
# see  https://github.com/wradlib/wradlib/blob/8f125836f28582d31119dca76a9e13f7297987c4/wradlib/georef/rect.py
#
# usage:
# from radolan_rv_coord_proj_kugel import getRadolanRvCoord
# (x, y) = getRadolanRvCoord(lat, lon)
#
from math import sin, cos, radians

def getRadolanRvCoord(lat, lon):
    return getMatrixCoord((1200, 1100), lat, lon)

matrix_definitions = {
    (1200, 1100): {'dy':600 , 'dx':470},
    (900, 900): {'dy':450 , 'dx':450},
}

def getMatrixCoord(matrixDimensionYX, lat, lon):
    matrix_definition = matrix_definitions[matrixDimensionYX]
    assert matrix_definition, 'unknown matrix dimension: ' + matrixDimensionYX
    #print(matrix_definition)
    (x_0, y_0) = getRadolanCoord(51, 9)
    #print(x_0, y_0)
    x_0 = x_0 - matrix_definition['dx']
    y_0 = y_0 - matrix_definition['dy']
    #print(x_0, y_0)
    (x, y) = getRadolanCoord(lat, lon)
    #print(x, y)
    x = round(x - x_0, 0)
    y = round(y - y_0, 0)
    #print(x, y)
    assert x <= matrixDimensionYX[1] and y <= matrixDimensionYX[0], "provided lan/lot are outside of the matrix"
    return (int(x), int(y))

def getRadolanCoord(lat, lon):
    phi_0 = radians(60)
    phi_m = radians(lat)
    lam_0 = 10
    lam_m = lon
    lam = radians(lam_m - lam_0)
    er = 6370.040
    m_phi = (1 + sin(phi_0)) / (1 + sin(phi_m))
    cos_phi_m = cos(phi_m)
    x = er * m_phi * cos_phi_m * sin(lam)
    y = -er * m_phi * cos_phi_m * cos(lam)
    return (x, y)

if __name__ == "__main__":
    coords = [
        ( 55.86584289, 1.435612143), # NW
        ( 55.84848692, 18.76728172), # NO
        ( 45.68358331, 16.60186543), # SO
        ( 45.69587048, 3.551921296)  # SW
    ]
    for coord in coords:
        print(coord)
        (x, y)=getRadolanRvCoord(*coord)
        print(x, y)

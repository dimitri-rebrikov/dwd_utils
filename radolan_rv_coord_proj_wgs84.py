# converts lat, lon coordinates 
# to RADOLAN RV matrix x, y coordinates 
# based on the ball (german "kugel") earth model
# using the proj library
# see  https://www.dwd.de/DE/leistungen/radarprodukte/formatbeschreibung_rv.pdf
#
# usage:
# from radolan_rv_coord_proj_kugel import getRadolanRvCoord
# (x, y) = getRadolanRvCoord(lat, lon)
#
from pyproj import Transformer
transformer=Transformer.from_proj("EPSG:4326", "+proj=stere +lat_0=90 +lat_ts=60 +lon_0=10 +a=6378137 +b=6356752.3142451802 +no_defs +x_0=543696.83521776402 +y_0=3622088.8619310018")

def getRadolanRvCoord(lat, lon):
    (x, y)=transformer.transform(lat, lon)
    return((int(round(x/1000, 0)), int(round(y/1000+1200, 0))))

if __name__ == "__main__":
    coords = [
        ( 55.86208711, 1.463301510), # NW
        ( 55.84543856, 18.73161645), # NO
        ( 45.68460578, 16.58086935), # SO
        ( 45.69642538, 3.566994635)  # SW
    ]
    for coord in coords:
        print(coord)
        (x, y)=getRadolanRvCoord(*coord)
        print(x, y)
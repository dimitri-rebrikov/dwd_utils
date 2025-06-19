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
transformer=Transformer.from_proj("EPSG:4326", "+proj=stere +lat_ts=60 +lat_0=90 +lon_0=10 +x_0=543196.83521776402 +y_0=3622588.8619310022 +units=m +a=6378137 +b=6356752.3142451802 +no_defs")

def getRadolanRvCoord(lat, lon):
    (x, y)=transformer.transform(lat, lon)
    return((int(round(x/1000, 0)), int(round(y/1000, 0))*-1))

if __name__ == "__main__":
    coords = [
        ( 55.862087108249824, 1.463301510256666), # UL/NW
        ( 55.845438563255755, 18.73161645466747), # UR/NO
        ( 45.68460578137082, 16.580869348598274), # LR/SO
        ( 45.696425377390064, 3.5669946350078914)  # LL/SW
    ]
    for coord in coords:
        print(coord)
        (x, y)=getRadolanRvCoord(*coord)
        print(x, y)
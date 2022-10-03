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
transformer=Transformer.from_proj("EPSG:4326", "+proj=stere +lat_0=90 +lat_ts=60 +lon_0=10 +a=6370040 +b=6370040 +no_defs +x_0=543462.16692185658 +y_0=3608644.7242655745")

def getRadolanRvCoord(lat, lon):
    (x, y)=transformer.transform(lat, lon)
    return((int(round(x/1000, 0)), int(round(y/1000+1200, 0))))

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
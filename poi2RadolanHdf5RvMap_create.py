from poi2LatLonMap import poi2LatLonMap
from radolan_rv_coord_proj_wgs84_hdf5 import getRadolanRvCoord

poi2RadolanHdf5RvMap={}

for poi in poi2LatLonMap.items():
    poi2RadolanHdf5RvMap[poi[0]] = getRadolanRvCoord(poi[1]['lat'], poi[1]['lon'])

with open('poi2RadolanHdf5RvMap.py', 'w') as file:
    file.write('poi2RadolanHdf5RvMap=')
    file.write(repr(poi2RadolanHdf5RvMap))
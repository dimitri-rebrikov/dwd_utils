from poi2LatLonMap import poi2LatLonMap
from radolan_rv_coord_proj_kugel import getRadolanRvCoord
from pickle import dump

poi2RadolanRvMap={}

for poi in poi2LatLonMap.items():
    poi2RadolanRvMap[poi[0]] = getRadolanRvCoord(poi[1]['lat'], poi[1]['lon'])

with open('poi2RadolanRvMap.py', 'w') as file:
    file.write('poi2RadolanRvMap=')
    file.write(repr(poi2RadolanRvMap))
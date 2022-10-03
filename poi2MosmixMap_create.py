from poi2LatLonMap import poi2LatLonMap
from mosmix_station import StationList

poi2MosmixMap={}
stations = StationList()

for poi in poi2LatLonMap.items():
    poi2MosmixMap[poi[0]] = stations.getNearestStation(poi[1]['lat'], poi[1]['lon'])['station'].id

with open('poi2MosmixMap.py', 'w') as file:
    file.write('poi2MosmixMap=')
    file.write(repr(poi2MosmixMap))
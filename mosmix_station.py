import re
from math import cos, sqrt
from urllib.request import urlopen, urlretrieve
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import tempfile

class MosmixStation:

    def __init__(self, id, lat, lon, name=None, elevation=None):
         self.id = id
         self.name = name
         self.lat = lat
         self.lon = lon
         self.elevation = elevation

    def distanceTo(self, lat, lon):
        dx = 111.3 * cos((self.lat + lat) / 2 * 0.01745) * (self.lon - lon)
        dy = 111.3 * (self.lat - lat)
        return sqrt((dx*dx)+(dy*dy))
    

class StationList:

    station_list_url = "https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication"
    station_pattern = re.compile("^[0-9]{4,5}")

    def __init__(self):
        self.stations = StationList.__getStations()

    @staticmethod
    def __is_station(row):
        return StationList.station_pattern.match(row)

    @staticmethod
    def __convert_to_string(row):
        return row.decode(encoding='latin_1', errors='strict')

    @staticmethod
    def __convert_to_station(row):
        return MosmixStation(
            id = row[0:5].strip(),
            name = row[11:31].strip(),
            lat = StationList.__convert_minutes(row[32:38]),
            lon = StationList.__convert_minutes(row[39:46])
        )

    @staticmethod
    def __convert_minutes(coordinates):
        grad, minutes = coordinates.split('.')
        return float(grad) + (float(minutes)/60)

    @staticmethod
    def __getStations():
       return list(map(StationList.__convert_to_station, 
                    filter(StationList.__is_station, 
                        map(StationList.__convert_to_string,
                            urlopen(StationList.station_list_url)))))

    def getNearestStation(self, lat, lon):
        distance = -1
        for curSt in self.stations:
            curDistance = curSt.distanceTo(lat,lon)
            if distance == -1 or distance > curDistance:
                st = curSt
                distance = curDistance
                # print(vars(st), distance)
        return {
           "station" : st,
           "distance" : distance
        }


if __name__ == "__main__":
    #
    # usage examples
    #

    # list all mosmix stations
    # for s in StationList().stations:
    #     print(vars(s))

    # get the neareast mosmix station for the provided coordinates 
    st = StationList().getNearestStation(48.713626047254, 9.20206874969351)
    print(vars(st['station']), st['distance'])

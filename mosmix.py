from asyncio.windows_events import NULL
import re
import math
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET

class MosmixStation:

    urlPattern = "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_L/single_stations/{id}/kml/MOSMIX_L_LATEST_{id}.kmz"

    def __init__(self, id, lat, lon, name=None, elevation=None):
         self.id = id
         self.name = name
         self.lat = lat
         self.lon = lon
         self.elevation = elevation

    def distanceTo(self, lat, lon):
        dx = 111.3 * math.cos((self.lat + lat) / 2 * 0.01745) * (self.lon - lon)
        dy = 111.3 * (self.lat - lat)
        return math.sqrt(pow(dx,2)+pow(dy,2))
    
    def getData(self, elementNameList=[]):
        url = MosmixStation.urlPattern.replace('{id}', self.id)
        content = urlopen(url)
        zf = ZipFile(BytesIO(content.read()))
        file = zf.open( zf.namelist()[0])
        root = ET.parse(file).getroot()
        # print(root)
        times = root.findall('./{*}Document/{*}ExtendedData/{*}ProductDefinition/{*}ForecastTimeSteps/{*}TimeStep')
        timesArr = []
        for time in times:
            timesArr.append(time.text)
            # print(time.text)

        name = root.find('./{*}Document/{*}Placemark/{*}name').text
        # print(name.text)

        description = root.find('./{*}Document/{*}Placemark/{*}description').text
        # print(description.text)

        forecasts = root.findall('./{*}Document/{*}Placemark/{*}ExtendedData/{*}Forecast')
        forecastMap = {}
        for forecast in forecasts:
            forecastName = forecast.attrib['{https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd}elementName']
            if len(elementNameList) == 0 or forecastName in elementNameList:
                # print(forecastName)
                forecastValue = forecast.find('./{*}value')
                forecastValues = re.split('\s+', forecastValue.text)
                # print(forecastValues)
                forecastMap[forecastName]=forecastValues

        coordinates = root.find('./{*}Document/{*}Placemark/{*}Point/{*}coordinates')
        #print(coordinates.text)
        lon, lat, elevation = coordinates.text.split(',')
        return {
            'stationData' : {'name':name, 'description':description, 'lat':lat, 'lon':lon, 'elevation':elevation},
            'times' : timesArr,
            'forecasts' :forecastMap
        }

class StationList:

    station_list_url = "https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication"
    station_pattern = re.compile("^[0-9\-]{5}")

    @staticmethod
    def __is_station(row):
        return StationList.station_pattern.match(row)

    @staticmethod
    def __convert_to_string(row):
        return row.decode(encoding='latin_1', errors='strict')

    @staticmethod
    def __convert_to_station(row):
        return MosmixStation(
            id = row[12:17].strip(),
            name = row[23:43].strip(),
            lat = StationList.__convert_minutes(row[44:50]),
            lon = StationList.__convert_minutes(row[51:58])
        )

    @staticmethod
    def __convert_minutes(coordinates):
        grad, minutes = coordinates.split('.')
        return float(grad) + (float(minutes)/60)

    @staticmethod
    def getStations():
        for s in map(StationList.__convert_to_station, 
                    filter(StationList.__is_station, 
                        map(StationList.__convert_to_string,
                            urlopen(StationList.station_list_url)))):
            yield(s)

    @staticmethod
    def getNearestStation(lat, lon):
        distance = -1
        for curSt in StationList.getStations():
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
    # for s in StationList.getStations():
    #     print(vars(s))

    # get the neareast mosmix station for the provided coordinates 
    st = StationList.getNearestStation(48.713626047254, 9.20206874969351)
    print(vars(st['station']), st['distance'])

    # get the mosmix data for the station 
    # for the possible data types see https://opendata.dwd.de/weather/lib/MetElementDefinition.xml
    fc = st['station'].getData({'TTT', 'FF'})
    print(fc)
import re
import math
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
        dx = 111.3 * math.cos((self.lat + lat) / 2 * 0.01745) * (self.lon - lon)
        dy = 111.3 * (self.lat - lat)
        return math.sqrt(pow(dx,2)+pow(dy,2))
    

class StationList:

    station_list_url = "https://www.dwd.de/DE/leistungen/met_verfahren_mosmix/mosmix_stationskatalog.cfg?view=nasPublication"
    station_pattern = re.compile("^[0-9\-]{5}")

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


class MosmixData:

    def __init__(self):
        self.stationList = StationList()

    def getSationsDataByCoords(self, latLonTupleList, elementNameList=None, hourList=None):
        latLonToStationMap = { latLon: self.stationList.getNearestStation(latLon[0], latLon[1])['station'].id for latLon in latLonTupleList }
        stationsDataMap = MosmixData.getStationsDataByIds(set(latLonToStationMap.values()), elementNameList, hourList)
        return {latLon : stationsDataMap[latLonToStationMap[latLon]] for latLon in latLonTupleList }

    @staticmethod
    def getStationsDataByIds(stationIdList, elementNameList=None, hourList=None):
        # print(stationIdList)
        with tempfile.NamedTemporaryFile(prefix="mosmix_", mode='rb', delete=False) as localKmzFile:
            # we need to store the kmz file locally as ZipFile needs random access to it
            urlretrieve("https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_S/all_stations/kml/MOSMIX_S_LATEST_240.kmz", localKmzFile.name)

            zf = ZipFile(localKmzFile)
            file = zf.open(zf.namelist()[0])
            context = ET.iterparse(file, events=("start", "end"))
            ns_dwd = "{https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd}"
            ns_kml = "{http://www.opengis.net/kml/2.2}"
            stationsData = {}
            for index, (event, elem) in enumerate(context):
                # Get the root element.
                if index == 0:
                    root = elem
                if event == "end":
                    if elem.tag == ns_dwd + "ForecastTimeSteps":
                        # print(elem.tag)
                        times = elem.findall('./{*}TimeStep')
                        #print(times)
                    elif elem.tag == ns_kml + "Placemark":
                        # print(elem.tag)
                        stationId = elem.find('./{*}name').text
                        # print(stationId)
                        if stationId in stationIdList:
                            stationsData[stationId] = MosmixData.__parsePlacemark(times, elem, elementNameList, hourList)
                            # print(stationsData[stationId])
                    root.clear()
            # print(stationsData)
            return stationsData

    @staticmethod
    def __parsePlacemark(times, placemark, elementNameList, hourList):
        timesArr = []
        for time in times:
            timesArr.append({'time':time.text, 'values':{}})
            # print(time.text)

        description = placemark.find('./{*}description').text
        # print(description.text)

        forecasts = placemark.findall('./{*}ExtendedData/{*}Forecast')
        for forecast in forecasts:
            forecastName = forecast.attrib['{https://opendata.dwd.de/weather/lib/pointforecast_dwd_extension_V1_0.xsd}elementName']
            if elementNameList == None or forecastName in elementNameList:
                # print(forecastName)
                forecastString = forecast.find('./{*}value').text.strip()
                # print('"'+forecastString+'"')
                forecastValues = re.split('\s+', forecastString)
                # print(forecastValues)
                for i, forecastValue in enumerate(forecastValues):
                    # print(forecastName, i, forecastValue)
                    timesArr[i]['values'][forecastName]=forecastValue
        
        if hourList != None:
            timesArr = MosmixData.__filterHours(hourList, timesArr)

        coordinates = placemark.find('./{*}Point/{*}coordinates')
        #print(coordinates.text)
        lon, lat, elevation = coordinates.text.split(',')
        return {
            'stationData' : {'description':description, 'lat':lat, 'lon':lon, 'elevation':elevation},
            'forecasts' : timesArr,
        }

    @staticmethod
    def __filterHours(hourList, timesArr):
        newArr = []
        nowHour = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for hour in hourList:
            def filterFunc(timeArrElem, desiredTime = nowHour + timedelta(hours=hour)):
                time = datetime.strptime(timeArrElem['time'].replace('Z', 'UTC'), '%Y-%m-%dT%H:%M:%S.%f%Z').replace(tzinfo=timezone.utc).replace(minute=0, second=0, microsecond=0) 
                # print(desiredTime, time)
                return time == desiredTime
            newArr.extend(filter(filterFunc, timesArr))
        return newArr



if __name__ == "__main__":
    #
    # usage examples
    #

    # list all mosmix stations
    # for s in StationList().stations:
    #     print(vars(s))

    # get the neareast mosmix station for the provided coordinates 
    # st = StationList().getNearestStation(48.713626047254, 9.20206874969351)
    # print(vars(st['station']), st['distance'])

    # get the mosmix data for coordinates
    # for the optional data types see https://opendata.dwd.de/weather/lib/MetElementDefinition.xml
    # the optional hour range represent the hours in the future started from now which have to included
    data = MosmixData().getSationsDataByCoords({(48.78827242522538, 9.194220320956434),(48.15743009625175, 11.567928277345185)}, {'TTT', 'FF'}, range(3,9))
    print(data)

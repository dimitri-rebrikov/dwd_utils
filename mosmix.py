import re
from math import cos, sqrt
from urllib.request import urlopen, urlretrieve, Request
from io import BytesIO
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import tempfile

class MosmixData:

    @staticmethod
    def __getMosmixFileUrl():
        return "https://opendata.dwd.de/weather/local_forecasts/mos/MOSMIX_S/all_stations/kml/MOSMIX_S_LATEST_240.kmz"

    @staticmethod
    def getMosmixDataTimestamp():
        return urlopen(Request(url=MosmixData.__getMosmixFileUrl(), method='HEAD')).getheader('last-modified')    

    @staticmethod
    def getStationsDataByIds(stationIdList, elementNameList=None, hourList=None):
        # print(stationIdList)
        with tempfile.NamedTemporaryFile(prefix="mosmix_", mode='rb', delete=False) as localKmzFile:
            # we need to store the kmz file locally as ZipFile needs random access to it
            urlretrieve(MosmixData.__getMosmixFileUrl(), localKmzFile.name)

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
                        elem.clear()
                    elif elem.tag == ns_kml + "Placemark":
                        # print(elem.tag)
                        stationId = elem.find('./{*}name').text
                        # print(stationId)
                        if stationId in stationIdList:
                            stationsData[stationId] = MosmixData.__parsePlacemark(times, elem, elementNameList, hourList)
                            # print(stationsData[stationId])
                        elem.clear()
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
                dstr = timeArrElem['time']
                time = datetime(int(dstr[:4]), int(dstr[5:7]), int(dstr[8:10]), int(dstr[11:13]), 0, 0, 0, timezone.utc)
                # print(desiredTime, time)
                return time == desiredTime
            newArr.extend(filter(filterFunc, timesArr))
        return newArr



if __name__ == "__main__":
    #
    # usage examples
    #

    # get the mosmix data for coordinates
    # for the optional data types see https://opendata.dwd.de/weather/lib/MetElementDefinition.xml
    # the optional hour range represent the hours in the future to be included started from now
    print(MosmixData.getMosmixDataTimestamp())
    from poi2MosmixMap import poi2MosmixMap
    data = MosmixData.getStationsDataByIds({poi2MosmixMap['70567'],poi2MosmixMap['10555']}, {'TTT', 'FF'}, range(3,9))
    print(data)

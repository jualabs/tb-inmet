import requests

metalist = []

#GET INMET HTML STATION DATA
site="http://www.inmet.gov.br/sonabra/maps/pg_mapa.php"
r = requests.get(site)

#PARSE HTML DATA
for l in r.iter_lines():
  line = l.lstrip(" ")
  if 'ESTA' in l:
     parts = line.split(" ")
     metadata = {
       'stationName': '',
       'stationCode': parts[2],
       'latitude': 0,
       'longitude': 0,
       'altitude': 0,
       'launchDate': '',
       'url': '',
       'stationState': '',
     }
     continue
  if 'var html' in line:
     data = line.split('<br>')
     for d in data:
        try:
           if d[0:3] == '<ta':
              metadata['url'] = d.split('<a href=')[1].split(" ")[0]
           elif d[0:3] == '</a':
              metadata['url'] = d.split('<a href=')[1].split(" ")[0]
           elif d[0:3] == 'Lat':
              metadata['latitude'] = d.split(" ")[1][:-1]
           elif d[0:3] == 'Lon':
              metadata['longitude'] = d.split(" ")[1][:-1]
           elif d[0:3] == 'Alt':
              metadata['altitude'] = d.split(':')[1].replace(" ","").split("metros")[0]
           elif d[0:2] == 'Gr':
              metadata['launchDate'] = d.split('Aberta em:')[1].replace(" ","").split("<br>")[0]
           else:
              continue
        except Exception as e:
           print(str(d))
           print(str(e))
           continue
  if 'var label' in line:
     parts = line.lstrip("var label =").strip(';').strip('\'')
     parts = l.lstrip(" ").lstrip("var label = ").replace(";","").replace("\n","").replace("\'","").replace(" - ",",").split(",")
     metadata['stationState'] = parts[0]
     metadata['stationName'] = parts[1]
     metalist.append(metadata)
     continue

#PRINT DATA FOR DEBUGGING
#for i in metalist:
#   print(i)

#NEXT STEPS
#GET STATIONS FROM TB
#CHECK IF THERE ARE NEW STATIONS
#CREATE NEW STATIONS AT TB
#DOWNLOAD DATA FROM THOSE NEW STATIONS SINCE ITS LAUNCH DATE (CRAWLER)

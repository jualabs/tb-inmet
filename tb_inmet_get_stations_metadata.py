#!/usr/bin/env python
# -*- coding: utf-8 -*-

f = open('metadata.html','r')

metalist = []

for line in f:
	metadata = {
		'stationName': '',
		'stationCode': '',
		'latitude': 0,
		'longitude': 0,
		'altitude': 0,
		'launchDate': '',
		'url': ''
	}	
	data = line.split('<br>')
	# get station name and code
	metadata['stationName'] = data[0].split('</b>')[1].replace(" ","").split("-")[0]
	code = data[0].split('</b>')[1].replace(" ","").split("-")[-1]
	if code[0] == 'A':
		metadata['stationCode'] = data[0].split('</b>')[1].replace(" ","").split("-")[-1]
	else:
		continue
		
	# get url, latitude, longitude, altitude and launch date
	for d in data:
		try: 
			if d[0:3] == '<ta':
				metadata['url'] = d.split('<a href=')[1].split(" ")[0]
			elif d[0:3] == '</a':
				metadata['url'] = d.split('<a href=')[1].split(" ")[0]
			elif d[0:3] == 'Lat':
				metadata['latitude'] = d.split(':')[1].replace(" ","").split("º")[0]
			elif d[0:3] == 'Lon':
				metadata['longitude'] = d.split(':')[1].replace(" ","").split("º")[0]
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
	metalist.append(metadata)

f.close()
f = open('stations.csv','w')
f.write('stationName;stationCode;latitude;longitude;altitude;launchDate;url\n')
for m in metalist:
	f.write(m['stationName'] + ';' +
			m['stationCode'] + ';' +
			m['latitude'] + ';' +
			m['longitude'] + ';' +
			m['altitude'] + ';' +
			m['launchDate'] + ';' +
			m['url'] + '\n')
f.close()

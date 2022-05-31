import os

gladeFiles = []

for x in os.walk('../gtk'):
	for y in x[2]:
		if y.find('.glade') == -1 or y.find('glade~') != -1:
			continue

		gladeFiles += [os.path.join(x[0], y)]


icons = []

for x in gladeFiles:
	f = open(x, 'r')
	data = f.read()
	f.close()

	# Get all strings surrounded by property 
	strings = []
	
	dataIName = data.split('<property name="icon-name">')[1:]
	for x in dataIName:
		if x.find('</property>') == -1:
			continue

		strings += [x.split('</property>')[0]]

	dataStock = data.split('<property name="icon-name">')[1:]
	for x in dataStock:
		if x.find('</property>') == -1:
			continue

		strings += [x.split('</property>')[0]]

	for y in strings:
		if y in icons:
			continue
	
		icons += [y]


def findIcon(x):
	# search x in /usr/share/icons/WhiteSur-dark/ recursively: if it is a link, get the original path
	for y in os.walk('/usr/share/icons/WhiteSur-dark/'):
		for z in y[2]:
			if z == x:
				return os.path.join(y[0], z)
	

for x in icons:
	l = findIcon(x + '.svg')
	if not l:
		print ('NOTFOUND:', x)
		continue

	# copy l to ../data/icons/
	os.system('cp -L ' + l + ' ../data/icons/')

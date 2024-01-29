import os

gladeFiles = []

for x in os.walk("../gtk"):
    for y in x[2]:
        if y.find(".glade") == -1 or y.find("glade~") != -1:
            continue

        gladeFiles += [os.path.join(x[0], y)]


icons = []

for g_file in gladeFiles:
    f = open(g_file, "r")
    data = f.read()
    f.close()

    # Get all strings surrounded by property
    strings = []

    dataIName = data.split('<property name="icon-name">')[1:]
    for iprop in dataIName:
        if iprop.find("</property>") == -1:
            continue

        strings += [iprop.split("</property>")[0]]

    dataStock = data.split('<property name="icon-name">')[1:]
    for data in dataStock:
        if data.find("</property>") == -1:
            continue

        strings += [data.split("</property>")[0]]

    for y in strings:
        if y in icons:
            continue

        icons += [y]


def findIcon(x):
    # search x in /usr/share/icons/WhiteSur-dark/ recursively: if it is a link,
    # get the original path
    for y in os.walk("/usr/share/icons/WhiteSur-dark/"):
        for z in y[2]:
            if z == x:
                return os.path.join(y[0], z)


for icn in icons:
    l_icn = findIcon(icn + ".svg")
    if not l_icn:
        print("NOTFOUND:", icn)
        continue

    # copy l to ../data/icons/
    os.system("cp -L " + l_icn + " ../data/icons/")

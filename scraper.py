import requests
import json
from bs4 import BeautifulSoup
url = "http://pathofexile.gamepedia.com/Active_Skills"
page = requests.get(url).text
soup = BeautifulSoup(page)
gems = {}
for span in soup.findAll("span", {"class": "gem-link"}):
    url = "http://pathofexile.gamepedia.com" + span.find("a")['href']
    print url

    page = requests.get(url).text
    soup = BeautifulSoup(page)
    gem = {'levels': {}}

    columns = {}
    for tr in soup.find("table", {"class": "GemLevelTable"}).find_all('tr'):
        trs = tr.find_all('th')
        if len(trs) > 2:
            for i, th in enumerate(trs):
                search = "".join(unicode(t) for t in th.contents)
                if "Dexterity" in search:
                    columns[i] = "Dex"
                if "Strength" in search:
                    columns[i] = "Str"
                if "Intelligence" in search:
                    columns[i] = "Int"
                if i == (len(trs) - 2):
                    columns[i] = th.contents[0].strip()
                if "Level" in search:
                    columns[i] = "Level"
                if "Required Level" in search:
                    columns[i] = "Required Level"
                if i == (len(trs) - 1):
                    columns[i] = "Exp"
        else:
            data = {}
            for i, td in enumerate(tr.findChildren()):
                try:
                    data[columns[i]] = td.contents[0].strip()
                except KeyError:
                    pass
            gem['levels'][data['Level']] = data

    gem['effects'] = []
    for div in soup.findAll("div", {"class": "GemInfoboxModifier"}):
        gem['effects'].append(div.get_text().strip())

    desc_node = soup.find("div", {"class": "GemInfoboxDescription"})
    if desc_node:
        gem['description'] = desc_node.get_text().strip()
    gem['name'] = soup.find("div", {"class": "GemInfoboxHeaderName"}).get_text().strip()
    for tr in soup.find("table", {"class": "GemInfoboxInfo"}).findAll("tr"):
        key, val = tr.findChildren('td')
        gem[key.contents[0].strip()] = val.get_text().strip()

    print json.dumps(gem)
    gems[gem['name']] = gem

print "\n\n\n\n\n"
print json.dumps(gems, indent=4)
json.dump(gems, open("gems.json", "w"), indent=4)

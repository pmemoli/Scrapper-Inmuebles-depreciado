import requests
import bs4
import re

def getFloat(text):
	return re.findall(r'[0-9]+,[0-9]+', text)[0].replace(',', '.')

def dolarPesoValue():
	re = requests.get('https://www.precio-dolar.com.ar/').text
	soup = bs4.BeautifulSoup(re, 'html.parser')
	return float(getFloat(soup.find('td', class_ = 'pocket-row-right').text))

dolarPesoValue()
import requests
import bs4
import re
import shelve
import os
import time
import openpyxl
from pandas import DataFrame, ExcelWriter
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


#Get current month.
datetimeObject = datetime.datetime.now()
keyMes = int(datetimeObject.month) - 1
año = datetimeObject.year
meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
mesActual = meses[keyMes]

#Create directories in shelve data and excel files accordint to current year and month.
os.makedirs('..\\..\\Excel Files\\Argenprop\\%s\\%s' % (año, mesActual), exist_ok = True)
os.makedirs('.\\Shelve Data\\%s\\%s' % (año, mesActual), exist_ok = True)

#Regexes necesarios.
localidadRegex = re.compile(r'en Venta en (.+)')

#Function required to apply regex inside a class.
def applyRegex(compiledRegex, text):
	return re.findall(compiledRegex, text)

#Function to make shelve more abstract and easier to use.
def openShelve(shelveName):
	shelveFile = shelve.open(shelveName)
	returnList = shelveFile[shelveName]
	shelveFile.close()
	return returnList

#Get Integer
def getInt(text):
	return re.findall(r'[0-9]+', text)[0]

def getFloat(text):
	return re.findall(r'[0-9]+,[0-9]+', text)[0].replace(',', '.')

def dolarPesoValue():
	re = requests.get('https://www.precio-dolar.com.ar/').text
	soup = bs4.BeautifulSoup(re, 'html.parser')
	return float(getFloat(soup.find('td', class_ = 'pocket-row-right').text))


class ArgenpropScrapper:
	def __init__(self, localidad = None, tipoIntercambio = 'Ambos', tipoPropiedad = 'Ambos'):
		#Selenium settings
		chromeDriverPath = '..\\..\\chromedriver.exe'
		options = Options()
		options.add_argument('--headless')
		self.browser = webdriver.Chrome(options = options, executable_path = chromeDriverPath)	

		#Location to be scrapped.
		self.localidad = localidad

		#Dictionary that holds the data from scrapping.
		self.propertyDict = {
			'nombre' : [],
			'tipoPropiedad' : [],
			'tipoOperacion' : [],
			'USD/Total depto':[],
			'USD/m2':[],
			'ARG/Expensas':[],
			'localidad' : [],
			'superficieCubierta' : [],
			'superficieDescubierta' : [],
			'dormitorios' : [],
			'cocheras' : [],
			'baños' : [],
			'antiguedad' : [],
			'patio':[],
			'controlAcceso':[],
			'SUM':[],
			'piscina':[],
			'gym':[],
			'link':[]
		}

		#If the class contains no arguments then pass, else search for links according to localidad.
		if localidad != None:
			#try:
			self.getLinks(tipoIntercambio, tipoPropiedad)
			#except:
				#print('Argenprop may not be available right now, try later.')

		self.linkList = []



	#Method that gets the links from self.localidad.
	def getLinks(self, tipoIntercambio = None, tipoPropiedad = None, finalLink = None):

		if finalLink == None:
			print('Consiguiendo links de %s...' % self.localidad)

			link = 'https://www.argenprop.com/'

			self.browser.get(link)

			time.sleep(2)

			searchBar = self.browser.find_element_by_name('LocationSearch.LocationTerm')
			searchBar.send_keys(self.localidad)

			time.sleep(2)

			elementsFound = self.browser.find_elements_by_css_selector('ol.show li')

			elementsFound[0].click()

			time.sleep(3)

			#Acquired Link and distinction by property trade type.
			searchedLink = self.browser.current_url


			#Change link acquired depending on what properties are being searched.
			if tipoIntercambio == 'Ambos':
				properLink = searchedLink.replace('-venta', '')

			elif tipoIntercambio == 'Venta':
				properLink = searchedLink

			elif tipoIntercambio == 'Alquiler':
				properLink = searchedLink.replace('-venta', '-alquiler')


			#Cambiar en base a casa/departamento
			if tipoPropiedad == 'Ambos':
				finalLink = properLink.replace('departamento', 'inmuebles')

			elif tipoPropiedad == 'Casa':
				finalLink = properLink.replace('departamento', 'casa')

			elif tipoPropiedad == 'Departamento':
				finalLink = properLink


			print('Se consiguio el link: %s' % finalLink)

		#Scrapping links with bs4.
		links = []
		numeroPagina = 1
		originalLink = finalLink

		while True:
			print('Consiguiendo links de: %s...' % finalLink)
			re = requests.get(finalLink).text
			soup = bs4.BeautifulSoup(re, 'html.parser')

			listingContainer = soup.find('div', class_ = 'listing-container')

			if len(listingContainer.find_all('a')) == 0:
				break

			for i in listingContainer.find_all('a'):
				if i.get('href') != None:
					if i.get('href') == '/':
						break
					else:
						propertyLink = 'https://www.argenprop.com' + i.get('href')
						links.append(propertyLink)

			numeroPagina += 1
			finalLink = originalLink + '-pagina-%s' % numeroPagina

		self.linkList = links

		print('Se consiguieron links de %s propiedades' % len(links))

		self.browser.quit()

		self.ScrapeLinkList()


	def scrapeLink(self, link):
		#Setting up bs4.
		re = requests.get(link).text
		soup = bs4.BeautifulSoup(re, 'html.parser')

		#Finding price in dollars.
		priceType = soup.find('p', class_ = 'titlebar__price').find('span').text
		print(priceType)

		if 'Consultar precio' in priceType:
			return None


		price = int(getInt(soup.find('p', class_ = 'titlebar__price').text.replace('.', '')))

		#Tipo propiedad.
		if 'departamento' in link:
			tipoPropiedad = 'Departamento'
		elif 'casa' in link:
			tipoPropiedad = 'Casa'
		elif 'terreno' in link:
			tipoPropiedad = 'Terreno'

		#Expensas de existir.
		expensas = None
		if len(soup.find_all('p', class_ = 'property-titlebar-sub-header')) == 1:
			expensas = int(getInt(soup.find_all('p', class_ = 'property-titlebar-sub-header')[0].text.replace('.', '')))

		if 'USD' in priceType:
			USDprice = int(price)
		elif '$' in priceType:
			USDprice = round(int(price) / dolarPesoValue())

		#Finding the name of the property.
		propertyName = soup.find('h3', class_ = 'titlebar__address').text


		#Superficie cubierta, dormitorios, banos, antiguedad.
		superficieDescubierta, superficieCubierta, dormitorios, baños, antiguedad, cocheras = 0, None, None, None, None, 0
		mainFeatures = soup.find('ul', class_ = 'property-main-features')

		for i in mainFeatures.find_all('li'):
			if 'Superficie cubierta' in i.find('p').text:
				superficieCubierta = int(getInt(i.find('span').text))

			elif 'Dormitorios' in i.find('p').text:
				dormitorios = int(getInt(i.find('span').text))

			elif 'Baños' in i.find('p').text:
				baños = int(getInt(i.find('span').text))

			elif 'Antigüedad' in i.find('p').text or 'Antiguedad' in i.find('p').text:
				if 'A estrenar' in i.find('span').text or 'A Estrenar' in i.find('span').text:
					antiguedad = 0
				else:
					antiguedad = int(getInt(i.find('span').text))

			if 'Superficie construible' in i.find('p').text:
				superficieDescubierta = int(getInt(i.find('span').text))

		#Superficie descubierta si existe.
		for i in soup.select('ul.property-features li'):
			if 'Sup. Descubierta' in str(i):
				superficieDescubierta = int(getInt(str(i)))

			if 'Cant. Cocheras' in str(i):
				cocheras = int(getInt(str(i)))



		#USD/m2.
		USDm2 = None
		if superficieCubierta != None:
			superficieTotal = superficieCubierta + superficieDescubierta
			USDm2 = round(price / superficieTotal)

		#Localidad.
		localidadHead = soup.find('h2', class_ = 'titlebar__title').text
		localidad = applyRegex(localidadRegex, localidadHead)[0]

		#Ammenities.
		descripcion = soup.find('section', class_ = 'description-web').text.lower()
		patio, controlAcceso, SUM, piscina, gym = 'No', 'No', 'No', 'No', 'No'
		if 'patio' in descripcion or 'jardin' in descripcion:
			patio = 'Si'

		if 'control acceso' in descripcion:
			controlAcceso = 'Si'

		if 'sum ' in descripcion:
			SUM = 'Si'

		if 'gym' in descripcion or 'gimnasio' in descripcion:
			gym = 'Si'

		if 'pileta' in descripcion or 'piscina' in descripcion:
			piscina = 'Si'

		#Tipo Operacion.
		tipoOperacion = None

		if 'venta' in link:
			tipoOperacion = 'Venta'
		elif 'alquiler' in link:
			tipoOperacion = 'Alquiler'

		#Append to dict.
		self.propertyDict['nombre'].append(propertyName)
		self.propertyDict['tipoPropiedad'].append(tipoPropiedad)
		self.propertyDict['tipoOperacion'].append(tipoOperacion)
		self.propertyDict['USD/Total depto'].append(USDprice)
		self.propertyDict['USD/m2'].append(USDm2)
		self.propertyDict['ARG/Expensas'].append(expensas)
		self.propertyDict['localidad'].append(localidad)
		self.propertyDict['superficieCubierta'].append(superficieCubierta)
		self.propertyDict['superficieDescubierta'].append(superficieDescubierta)
		self.propertyDict['dormitorios'].append(dormitorios)
		self.propertyDict['cocheras'].append(cocheras)
		self.propertyDict['baños'].append(baños)
		self.propertyDict['antiguedad'].append(antiguedad)
		self.propertyDict['patio'].append(patio)
		self.propertyDict['controlAcceso'].append(controlAcceso)
		self.propertyDict['SUM'].append(SUM)
		self.propertyDict['piscina'].append(piscina)
		self.propertyDict['gym'].append(gym)
		self.propertyDict['link'].append(link)


	def ScrapeLinkList(self):
		totalNumber = len(self.linkList)
		linksScraped = 0

		print('Scrapeando Links: \n')

		for i in self.linkList:
			try:
				self.scrapeLink(i)
				linksScraped += 1
				percentage = str(round((linksScraped / totalNumber) * 100)) + '%'
				print(percentage)	
			except:
				print('Hubo un error con este link: %s' % i)				
		
		self.dictToExcel(self.propertyDict)


	#Creates an excel file containing the data from self.propertyDict.
	def dictToExcel(self, dictionary, name = None):
		print('Creating excel file with the data scrapped...')
		myDF = DataFrame(dictionary)
		if name == None:
			writer = ExcelWriter('..\\..\\Excel Files\\Argenprop\\%s\\%s\\%s.xlsx' % (año, mesActual, self.localidad + ' ' +  datetime.datetime.today().strftime('%d-%m-%Y')))
		else:
			writer = ExcelWriter('..\\..\\Excel Files\\Argenprop\\%s\\%s\\%s.xlsx' % (año, mesActual, name + ' ' + datetime.datetime.today().strftime('%d-%m-%Y')))

		myDF.to_excel(writer)
		writer.save()
		print('Done! Saved in Excel Files directory')



testLink = 'https://www.argenprop.com/departamento-venta-partido-san-isidro'


if __name__ == '__main__':
	AirBnB = ArgenpropScrapper()
	AirBnB.scrapeLink(testLink)
	print(AirBnB.propertyDict)


	print('\nFinished')

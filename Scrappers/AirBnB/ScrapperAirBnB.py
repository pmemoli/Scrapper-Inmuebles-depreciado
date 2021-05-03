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

#Idea: Buscar Precio promedio de inmuebles por localidad de San martin de los andes, Bariloche y Villa la Angostura.

#TODO: Conseguir el link que redirectea la pagina automaticamente

#Get current month.
datetimeObject = datetime.datetime.now()
keyMes = int(datetimeObject.month) - 1
año = datetimeObject.year
meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
mesActual = meses[keyMes]


#Create directories in shelve data and excel files accordint to current year and month.
os.makedirs('..\\..\\Excel Files\\AirBnB\\%s\\%s' % (año, mesActual), exist_ok = True)
os.makedirs('.\\Shelve Data\\%s\\%s' % (año, mesActual), exist_ok = True)

#Regexes needed and applyRegex function due to re not working inside classes. (for some unknown reason)
regexLinksAvailable = re.compile(r'[0-9]+ a ([0-9]+)')
regexAvgReview = re.compile(r'(\d,\d+) ')
regexNumberReviews = re.compile(r'(\d+) evaluaci')
regexLocationTwo = re.compile(r'(.+), (.+), (.+)')
regexLocationOne = re.compile(r'(.+), (.+)')
regexPrecioPesosComa = re.compile(r'(\d,\d+) ARS')
regexDolares = re.compile(r'(\$ \d+)')
regexDolares1 = re.compile(r'(\$\d+)')
regexPrecioPesosNoComa = re.compile(r'(\d+) ARS')
regexDepartamento = re.compile(r'departamento|loft', re.IGNORECASE)
regexCasa = re.compile(r'cabaña|casa|bungalow', re.IGNORECASE)
regexHotel = re.compile(r'hotel', re.IGNORECASE)
regexHostel = re.compile(r'hostel', re.IGNORECASE)
regexHabitacionPrivada = re.compile(r'habitación privada', re.IGNORECASE)



regexDormitorio = re.compile(r'([0-9]+) dormitorio')
regexHuesped = re.compile(r'([0-9]+) hu')
regexCama = re.compile(r'([0-9]+) cama')
regexBaño = re.compile(r'([0-9]+) baño')



regexReseñaProm = re.compile(r'(.+)\(')
regexCantReseñas = re.compile(r'\(.+\)')

#Function required to apply regex inside a class.
def applyRegex(compiledRegex, text):
	return re.findall(compiledRegex, text)

#Function to make shelve more abstract and easier to use.
def openShelve(shelveName):
	shelveFile = shelve.open(shelveName)
	returnList = shelveFile[shelveName]
	shelveFile.close()
	return returnList

def getInt(text):
	return re.findall(r'[0-9]+', text)

def openShelve(shelveName):
	pass

class AirBnBScrapper:
	def __init__(self, linkList = None):
		#Selenium settings
		chromeDriverPath = '..\\..\\chromedriver.exe'
		options = Options()
		options.add_argument('--headless')
		self.browser = webdriver.Chrome(options = options, executable_path = chromeDriverPath)	

		#Dictionary that holds the data from scrapping.
		self.propertyDict = {
			'nombre' : [],
			'tipoPropiedad' : [],
			'localidad' : [],
			'huespedes' : [],
			'dormitorios' : [],
			'camas' : [],
			'baños' : [],
			'precioPorDiaUSD' : [],
			'tasaOcupacionMesActual' : [],
			'tasaOcupacionMesSiguiente' : [],
			'reseñaPromedio' : [],
			'cantidadReseñas' : [],
			'superHost' : [],
			'link' : [],
		}

		#linkList encompasses the links given to the object, or None if nothing is given.
		self.linkList = linkList


	def getLinks(self, searchName):
		#Tools for scrapping
		link = 'https://www.airbnb.com.ar/s/' + searchName.replace(' ', '-') + '/homes?display_currency=USD'

		linkList = []

		pageNumber = 1

		while True:	
			self.browser.get(link)

			time.sleep(5)

			re = self.browser.page_source

			soup = bs4.BeautifulSoup(re, 'html.parser')

			for i in soup.find_all('div', class_ = '_8ssblpx'):
				individualProperty = []

				for possibleLink in i.find_all('a'):
					if possibleLink.get('href') != None:
						link = 'https://www.airbnb.com.ar' + possibleLink.get('href')
						individualProperty.append(link)
						break


				if i.find('div', class_ = '_167qordg') != None:
					tipoPropiedad = i.find('div', class_ = '_167qordg').text.split()[0]
				else:
					tipoPropiedad = ''

				individualProperty.append(tipoPropiedad)


				linkList.append(individualProperty)


			found = False
			for i in soup.find_all('li', class_ = '_i66xk8d'):
				if i.find('a') != None:
					if i.find('a').get('href') != None:
						nextLink = 'https://www.airbnb.com.ar' + i.find('a').get('href')
						found = True
						break


			link = nextLink


			print('page %d scraped...' % pageNumber)
			pageNumber += 1


			if not found:
				break


		self.linkList = linkList
		



	#Scrapes a single link. (used alone mainly for testing, and as a function inside scrapeShelve)
	def ScrapeLink(self, chosenLink, append = False, stick = False, keyword = None):
		#Separate the tuple from chosenLink if the user wishes to append to dict (which implies a linkList is being used).
		if append == True:
			propertyLink = chosenLink[0]
			propertyType = chosenLink[1]

		else:
			propertyLink = chosenLink



		#Downloading text and parsing it with bs4. While loop serves to fix errors in downloading html.
		tries = 0
		while True:
			try:
				self.browser.get(propertyLink)

				time.sleep(8)

				re = self.browser.page_source

				soup = bs4.BeautifulSoup(re, 'html.parser')

				#Name
				propertyName = soup.find('h1', class_ = '_14i3z6h').text

				break

			except Exception as exc:
				print('Hubo un error descargando la pagina, intentando otra vez...')
				print(exc)
				self.browser.quit()

				chromeDriverPath = '..\\..\\chromedriver.exe'
				options = Options()
				options.add_argument('--headless')
				self.browser = webdriver.Chrome(options = options, executable_path = chromeDriverPath)
				tries += 1

				if tries > 5:
					return None


		#Location
		fullLocation = soup.find('span', class_ = '_13myk77s').text

		if keyword != None:
			villaLocation = False
			if keyword in fullLocation.lower():
				villaLocation = True

			#Description
			villaDescripcion = False

			try:
				description = soup.find('div', class_ = '_1y6fhhr').text.lower()
				if keyword in description:
					villaDescripcion = True

			except:
				if villaLocation == False:
					return None

			if not (villaDescripcion or villaLocation):
				return None


		#Characteristics
		huesped, dormitorio, cama, baño = 'No muestra', 0, 'No muestra', 'No muestra'
		for i in soup.find_all('div', class_ = '_tqmy57'):
			textHolder = i.text
			if textHolder != None:
				if 'huésped' in textHolder:
					huesped = int(applyRegex(regexHuesped, textHolder)[0])
				if 'dormitorio' in textHolder:
					dormitorio = int(applyRegex(regexDormitorio, textHolder)[0])
				if 'cama' in textHolder:
					cama = int(applyRegex(regexCama, textHolder)[0])
				if 'baño' in textHolder:
					baño = int(applyRegex(regexBaño, textHolder)[0])


		#Reviews
		avgReview, numberOfReviews = None, 0
		for i in soup.find_all('button', class_ = '_1wlymrds'):
			try:
				avgReview = applyRegex(regexReseñaProm, i.text)[0].replace(',', '.')
			except:
				pass

			try:
				numberOfReviews = applyRegex(regexCantReseñas, i.text)[0].replace('(', '').replace(')', '')
			except:
				pass
			



		#SuperHost
		superHost = 'No'
		for i in soup.find_all('span', class_ = '_nu65sd'):
			 if 'Superhost' in i.text or 'Superanfitrión' in i.text:
			 	superHost = 'Si'


		#Precio
		pricePerDayUSD = 'No Muestra'
		for i in soup.find_all('span', class_ = '_pgfqnw'):
			pricePerDayUSD = float(i.text.replace('$', ''))



		#Tasa ocupacion mes actual
		mesActualTable, mesPosteriorTable = soup.find_all('table', class_ = '_cvkwaj')[1], soup.find_all('table', class_ = '_cvkwaj')[2]

		mesActualOcupado, mesPosteriorOcupado = len(mesActualTable.find_all('td', class_ = '_z39f86g')), len(mesPosteriorTable.find_all('td', class_ = '_z39f86g'))
		mesActualLibre, mesPosteriorLibre = len(mesActualTable.find_all('td', class_ = '_12fun97')), len(mesPosteriorTable.find_all('td', class_ = '_12fun97'))
		
		tasaOcupacionMesActual = round((mesActualOcupado / (mesActualOcupado + mesActualLibre)) * 100)
		tasaOcupacionMesSiguiente = round((mesPosteriorOcupado / (mesPosteriorOcupado + mesPosteriorLibre)) * 100)




		#Append implies that link list is being used. Precio can be acquired.
		if append == True or stick == True:
			#Append data
			self.propertyDict['nombre'].append(propertyName)

			self.propertyDict['localidad'].append(fullLocation)

			self.propertyDict['huespedes'].append(huesped)
			self.propertyDict['dormitorios'].append(dormitorio)
			self.propertyDict['camas'].append(cama)
			self.propertyDict['baños'].append(baño)

			self.propertyDict['reseñaPromedio'].append(avgReview)
			self.propertyDict['cantidadReseñas'].append(numberOfReviews)

			self.propertyDict['tasaOcupacionMesActual'].append(tasaOcupacionMesActual)
			self.propertyDict['tasaOcupacionMesSiguiente'].append(tasaOcupacionMesSiguiente)

			#self.propertyDict['wifi'].append(Wifi)
			#self.propertyDict['estacionamientoPropiedad'].append(EstacionamientoPropiedad)
			#self.propertyDict['estacionamientoCalle'].append(EstacionamientoCalle)
			#self.propertyDict['serviciosBasicos'].append(ServiciosBasicos)
			#self.propertyDict['calefaccion'].append(Calefaccion)
			#self.propertyDict['patio'].append(Patio)
			#self.propertyDict['accesoLago'].append(AccesoLago)
			#self.propertyDict['accesoCosta'].append(AccesoCosta)

			self.propertyDict['superHost'].append(superHost)	
			self.propertyDict['link'].append(propertyLink)
			self.propertyDict['precioPorDiaUSD'].append(pricePerDayUSD)

			if append == True:
				self.propertyDict['tipoPropiedad'].append(propertyType)



	#Scrapes the entire link list.
	def scrapeLinkList(self, name, keyword_ = None):
		totalNumber = len(self.linkList)
		linksScraped = 0
		print('Scrapeando Links: \n')
		for i in self.linkList:
			try:
				self.ScrapeLink(i, append = True, keyword = keyword_)
				linksScraped += 1
				percentage = str(round((linksScraped / totalNumber) * 100)) + '%'
				print(percentage)

			except Exception as exc:
				print('Hubo un error con este link: %s' % i[0])
				print(exc)

		self.dictToExcel(self.propertyDict, name)



	#Creates an excel file containing the data from self.propertyDict.
	def dictToExcel(self, dictionary, name = None):
		print('Creating excel file with the data scrapped...')
		myDF = DataFrame(dictionary)
		writer = ExcelWriter('..\\..\\Excel Files\\AirBnB\\%s\\%s\\%s.xlsx' % (año, mesActual, name + ' ' + datetime.datetime.today().strftime('%d-%m-%Y')))

		myDF.to_excel(writer)
		writer.save()
		print('Done! Saved in Excel Files directory')



testLink = r'https://www.airbnb.com.ar/rooms/10318102?location=Villa%20La%20Angostura%2C%20Neuqu%C3%A9n%2C%20Argentina&source_impression_id=p3_1596317779_oLEhiIIVwoN9lolu'


nombre = 'villa la angostura'
#Only creates an Airbnb object if the file is run but not imported
if __name__ == '__main__':
	Airbnb = AirBnBScrapper()

	Airbnb.getLinks(nombre)

	Airbnb.scrapeLinkList(nombre, keyword_ = 'villa')
	
	#Airbnb.ScrapeLink(testLink, stick = True, keyword = 'villa')
	#print(Airbnb.propertyDict)

	Airbnb.browser.quit()
	exit()


	print('\nFinished')


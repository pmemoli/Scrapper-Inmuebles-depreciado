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
os.makedirs('..\\..\\Excel Files\\ZonaProp\\%s\\%s' % (año, mesActual), exist_ok = True)
os.makedirs('.\\Shelve Data\\%s\\%s' % (año, mesActual), exist_ok = True)

#Regexes needed and applyRegex function due to re not working inside classes. (for some unknown reason)
regexLinksAvailable = re.compile(r'[0-9]+ a ([0-9]+)')
regexAvgReview = re.compile(r'(\d,\d+) ')
regexNumberReviews = re.compile(r'(\d+) evaluaci')
regexLocationTwo = re.compile(r'(.+), (.+), (.+)')
regexLocationOne = re.compile(r'(.+), (.+)')
regexPrecioPesosComa = re.compile(r'(\d,\d+) ARS')
regexPrecioPesosNoComa = re.compile(r'(\d+) ARS')
regexDepartamento = re.compile(r'departamento|loft', re.IGNORECASE)
regexCasa = re.compile(r'cabaña|casa|bungalow', re.IGNORECASE)
regexHotel = re.compile(r'hotel', re.IGNORECASE)
regexHostel = re.compile(r'hostel', re.IGNORECASE)
regexHabitacionPrivada = re.compile(r'habitación privada', re.IGNORECASE)

#Function required to apply regex inside a class.
def applyRegex(compiledRegex, text):
	return re.findall(compiledRegex, text)

#Function to make shelve more abstract and easier to use.
def openShelve(shelveName):
	shelveFile = shelve.open(shelveName)
	returnList = shelveFile[shelveName]
	shelveFile.close()
	return returnList


def getFloat(text):
	return re.findall(r'[0-9]+,[0-9]+', text)[0].replace(',', '.')


def getInt(text):
	return re.findall(r'[0-9]+', text)[0]


def dolarPesoValue():
	re = requests.get('https://www.precio-dolar.com.ar/').text
	soup = bs4.BeautifulSoup(re, 'html.parser')
	return float(getFloat(soup.find('td', class_ = 'pocket-row-right').text))


class ZonaPropScrapper:
	def __init__(self, localidad = None, tipoIntercambio = 'Ambos', tipoPropiedad = 'Ambos'):
		#Selenium settings
		chromeDriverPath = '..\\..\\chromedriver.exe'
		#options = Options()
		#options.add_argument('--headless')
		self.browser = webdriver.Chrome(executable_path = chromeDriverPath)	

		#Location to be scrapped.
		self.localidad = localidad

		#Operation and property types
		self.tipoPropiedad = tipoPropiedad
		self.tipoIntercambio = tipoIntercambio

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
		if self.localidad != None:
			self.getLinks()

		self.linkList = []


	def createSeleniumBrowser(self):
		self.browser.quit()
		chromeDriverPath = '..\\..\\chromedriver.exe'
		#options = Options()
		#options.add_argument('--headless')
		self.browser = webdriver.Chrome(executable_path = chromeDriverPath)	

	def getLinks(self):
		#Construct link based on given types
		if self.tipoPropiedad == 'Ambos':
			tipoPropiedad = 'inmuebles'

		elif self.tipoPropiedad == 'Casa':
			tipoPropiedad = 'casas'

		elif self.tipoPropiedad == 'Departamento':
			tipoPropiedad = 'departamentos'


		if self.tipoIntercambio == 'Ambos':
			tipoOperacion = ''

		elif self.tipoIntercambio == 'Venta':
			tipoOperacion = 'venta'

		elif self.tipoIntercambio == 'Alquiler':
			tipoOperacion = 'alquiler'


		if tipoOperacion == '':
			link = 'https://www.zonaprop.com.ar/' + tipoPropiedad + '-' + self.localidad.lower().replace(' ', '-') + '.html'

			modifiableLink = 'https://www.zonaprop.com.ar/' + tipoPropiedad + '-' + self.localidad.lower().replace(' ', '-')

		else:
			link = 'https://www.zonaprop.com.ar/' + tipoPropiedad + '-' + tipoOperacion + '-' + self.localidad.lower().replace(' ', '-') + '.html'

			modifiableLink = 'https://www.zonaprop.com.ar/' + tipoPropiedad + '-' + tipoOperacion + '-' + self.localidad.lower().replace(' ', '-')


		searching = True

		links = []
		n = 1

		while searching:
			self.browser.get(link)

			time.sleep(5)

			source = self.browser.page_source

			soup = bs4.BeautifulSoup(source, 'html.parser')

			propertyLinks = soup.find_all('a', class_ = 'go-to-posting')
			for i in propertyLinks:
				links.append('https://www.zonaprop.com.ar' + i.get('href'))

			print('links acquired for page %s' % n)

			n += 1

			if soup.find('li', class_ = 'pag-go-next') == None:
				searching = False

			else:
				link = modifiableLink + '-pagina-%s' % n + '.html'

			self.createSeleniumBrowser()

			#link = modifiableLink + '-pagina-%s' % n + '.html'


		print('%d properties found' % len(links))

		self.linkList = links
		print(self.linkList)

		self.scrapeLinkList()






	def scrapeSingleLink(self, link):
		if '/complejo-' in link:
			return None


		self.browser.get(link)

		time.sleep(5)

		re = self.browser.page_source

		soup = bs4.BeautifulSoup(re, 'html.parser')

		nombre = soup.select('div.section-title h1')[0].text


		precioRaw = soup.find('div', class_ = 'price-items').text

		#Variables que se van a usar
		superficieTotal, superficieCubierta, dormitorios, baños, cochera, superficieDescubierta, usdM2, antiguedad, jardin, precio = None, None, 1, None, None, 0, None, None, 'No', None
		controlAcceso, gym, SUM, pileta, localidad = 'No', 'No', 'No', 'No', None

		if 'USD' in precioRaw:
			precio = int(getInt(precioRaw.replace('.', '')))

		elif '$' in precioRaw:
			precio = round(int(getInt(precioRaw.replace('.', ''))) / dolarPesoValue())

		#Property attributes
		for feature in soup.find_all('li', class_ = 'icon-feature'):
			if 'Superficie total' in feature.find('span').text:
				superficieTotal = int(getInt(feature.find('b').text))

			if 'Superficie cubierta' in feature.find('span').text:
				superficieCubierta = int(getInt(feature.find('b').text))

			if 'Dormitorios' in feature.find('span').text or 'Dormitorio' in feature.find('span').text:
				dormitorios = int(getInt(feature.find('b').text))

			if 'Baño' in feature.find('span').text or 'Baños' in feature.find('span').text:# or 'Toilettes' in feature.find('span').text:
				baños = int(getInt(feature.find('b').text))

			if 'Cochera' in feature.find('span').text or 'Cocheras' in feature.find('span').text:
				cochera = int(getInt(feature.find('b').text))

			if 'Antigüedad' in feature.find('span').text or 'Antiguedad' in feature.find('span').text:
				try:
					antiguedad = int(getInt(feature.find('b').text))
				except:
					antiguedad = 0


		#Superficie descubierta
		if superficieTotal != None and superficieCubierta != None:
			superficieDescubierta = superficieTotal - superficieCubierta


		#USD/Superficie total
		if superficieTotal != None and precio != None:
			usdM2 = round(precio / superficieTotal)

		#Expensas
		expensasBlock = soup.find('div', class_ = 'block-expensas')
		expensas = None
		if expensasBlock != None:
			expensas = getInt(expensasBlock.text.replace('.', ''))

		#Localidad
		locationBlock = soup.find('h2', class_ = 'title-location')
		if locationBlock != None:
			localidad = soup.find('h2', class_ = 'title-location').find('span').text.replace(',  ', '')

		#Jardin
		for i in soup.find_all('ul', class_ = 'section-bullets'):
			if 'Jardín' in i.text or 'Jardin' in i.text:
				jardin = 'Si'

		#Datos en la descripcion
		descripcionBox = soup.find('div', class_ = 'section-description')
		if descripcionBox != None:
			textoDescripcion = descripcionBox.text.lower()

			if jardin == None:
				if 'jardín' in textoDescripcion or 'jardin' in textoDescripcion or 'patio' in textoDescripcion:
					jardin = 'Si'

				if 'sum' in textoDescripcion or 'salon usos multiples' in textoDescripcion:
					SUM = 'Si'

				if 'piscina' in textoDescripcion or 'pileta' in textoDescripcion:
					pileta = 'Si'

				if 'control acceso' in textoDescripcion or 'alarma' in textoDescripcion or 'seguridad' in textoDescripcion:
					controlAcceso = 'Si'

				if 'gym' in textoDescripcion or 'gimnasio' in textoDescripcion:
					gym = 'Si'

		#Tipo Propiedad y Tipo Operacion
		propertyTypeBox = soup.find('ul', class_ = 'breadcrumb')
		tipoPropiedad = propertyTypeBox.find_all('li', class_ = 'bread-item')[1].text.replace('\n', '')

		if self.tipoPropiedad == 'Ambos':
			if 'Casa' in propertyTypeBox.text:
				tipoPropiedad = 'Casa'

			elif 'Departamento' in propertyTypeBox.text:
				tipoPropiedad = 'Departamento'
		else:
			tipoPropiedad = self.tipoPropiedad


		if self.tipoIntercambio == 'Ambos':
			if 'Comprar' in propertyTypeBox.text:
				tipoOperacion = 'Venta'

			elif 'Alquilar' in propertyTypeBox.text:
				tipoOperacion = 'Alquilar'
		
		else:
			tipoOperacion = self.tipoIntercambio



		#Doble comprobacion ammenities
		generalSections = soup.find_all('section', class_ = 'general-section')

		for i in generalSections:
			textoDescripcion = i.text.lower()
			if 'jardín' in textoDescripcion or 'jardin' in textoDescripcion or 'patio' in textoDescripcion:
				jardin = 'Si'

			if 'sum' in textoDescripcion or 'salon usos multiples' in textoDescripcion:
				SUM = 'Si'

			if 'piscina' in textoDescripcion or 'pileta' in textoDescripcion:
				pileta = 'Si'

			if 'control acceso' in textoDescripcion or 'alarma' in textoDescripcion or 'seguridad' in textoDescripcion:
				controlAcceso = 'Si'

			if 'gym' in textoDescripcion or 'gimnasio' in textoDescripcion:
				gym = 'Si'



		self.propertyDict['nombre'].append(nombre); self.propertyDict['tipoPropiedad'].append(tipoPropiedad); self.propertyDict['tipoOperacion'].append(tipoOperacion)
		self.propertyDict['USD/Total depto'].append(precio); self.propertyDict['USD/m2'].append(usdM2); self.propertyDict['ARG/Expensas'].append(expensas)
		self.propertyDict['localidad'].append(localidad); self.propertyDict['superficieCubierta'].append(superficieCubierta)
		self.propertyDict['superficieDescubierta'].append(superficieDescubierta); self.propertyDict['dormitorios'].append(dormitorios)
		self.propertyDict['cocheras'].append(cochera); self.propertyDict['baños'].append(baños); self.propertyDict['antiguedad'].append(antiguedad)
		self.propertyDict['patio'].append(jardin); self.propertyDict['controlAcceso'].append(controlAcceso); self.propertyDict['gym'].append(gym)
		self.propertyDict['link'].append(link); self.propertyDict['SUM'].append(SUM); self.propertyDict['piscina'].append(pileta)








	def scrapeLinkList(self, linkList = None):
		if linkList != None:
			scrapeList = linkList
		else:
			scrapeList = self.linkList


		totalNumber = len(scrapeList)
		linksScraped = 0
		print('Scrapeando Links: \n')
		for i in scrapeList:
			try:
				self.scrapeSingleLink(i)
				linksScraped += 1
				percentage = str(round((linksScraped / totalNumber) * 100)) + '%'
				print(percentage)
			except Exception as exc:
				print('Hubo un error con este link: %s' % i)
				print(exc)

			self.createSeleniumBrowser()

		#If passing it to excel causes an error the progress is saved with shelve.

		self.dictToExcel(self.propertyDict, name = 'Villa la angostura')



	def dictToExcel(self, dictionary, name = None):
		print('Creating excel file with the data scrapped...')
		myDF = DataFrame(dictionary)
		if name == None:
			writer = ExcelWriter('..\\..\\Excel Files\\ZonaProp\\%s\\%s\\%s.xlsx' % (año, mesActual, self.localidad + ' ' +  datetime.datetime.today().strftime('%d-%m-%Y')))
		else:
			writer = ExcelWriter('..\\..\\Excel Files\\ZonaProp\\%s\\%s\\%s.xlsx' % (año, mesActual, name + ' ' + datetime.datetime.today().strftime('%d-%m-%Y')))

		myDF.to_excel(writer)
		writer.save()
		print('Done! Saved in Excel Files directory')



textLink = 'https://www.zonaprop.com.ar/propiedades/semi-piso-de-3-ambientes-a-estrenar-en-san-isidro-46232831.html'

linkList = ['https://www.zonaprop.com.ar/propiedades/lotes-en-venta-en-b-los-rododendros.-villa-la-46291224.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-las-hortensias-42929957.html', 'https://www.zonaprop.com.ar/propiedades/cabana-en-venta-villa-la-angostura-46340196.html', 'https://www.zonaprop.com.ar/propiedades/calfuco-calfuco-villa-la-angostura-45991192.html', 'https://www.zonaprop.com.ar/propiedades/terreno-villa-la-angostura-46256294.html', 'https://www.zonaprop.com.ar/propiedades/casa-zorzal-46256331.html', 'https://www.zonaprop.com.ar/propiedades/lote-zorzal-46256345.html', 'https://www.zonaprop.com.ar/propiedades/complejo-girasoles-el-once-villa-la-angostura-45991201.html', 'https://www.zonaprop.com.ar/propiedades/4-ambientes-las-gaviotas-al-300-46324949.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-puerto-la-mansa-2-amb-con-costa-45704293.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-puerto-la-mansa-2-amb-con-costa-45704269.html', 'https://www.zonaprop.com.ar/propiedades/vista-azul-45639885.html', 'https://www.zonaprop.com.ar/propiedades/departamentos-villa-la-angostura-costa-lago-akol-46256428.html', 'https://www.zonaprop.com.ar/propiedades/lote.-av-7-lagos-al-100-32363947.html', 'https://www.zonaprop.com.ar/propiedades/lote.-ruta-40-al-1000-27470876.html', 'https://www.zonaprop.com.ar/propiedades/haakon-el-mercado-villa-la-angostura-45991179.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-7-702-n-43854073.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-puerto-manzano-46341770.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-32354009.html', 'https://www.zonaprop.com.ar/propiedades/barrio-dos-lagos-villa-la-angostura-45991172.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-43822384.html', 'https://www.zonaprop.com.ar/propiedades/lote.-ruta-40-al-100-40098156.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad-en-villa-la-angostura-2-casas-mas-depto-y-40741062.html', 'https://www.zonaprop.com.ar/propiedades/dos-lagos-villas-marinas-33299075.html', 'https://www.zonaprop.com.ar/propiedades/cabana-en-venta-villa-la-angostura-46291205.html', 'https://www.zonaprop.com.ar/propiedades/casa-villa-la-angostura-46065734.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-3-302-n-33361400.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-43822389.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-5-501-c-43854069.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-m5-b-45484423.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-6-601-c-43907576.html', 'https://www.zonaprop.com.ar/propiedades/lote-zorzal-46329680.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-5-502-c-43854070.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-43822386.html', 'https://www.zonaprop.com.ar/propiedades/lote.-av-7-lagos-al-100-40097992.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-5-505-n-43854080.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-3-301-c-33361383.html', 'https://www.zonaprop.com.ar/propiedades/lote-michay-44462765.html', 'https://www.zonaprop.com.ar/propiedades/casa-villa-la-angostura-46060875.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-43822388.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-m4-a-45483998.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-43822387.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-las-hortensias-42929955.html', 'https://www.zonaprop.com.ar/propiedades/casa-5-ambientes.-ojo-de-dios-40097966.html', 'https://www.zonaprop.com.ar/propiedades/espectacular-casa-al-lago-nahuel-huapi!-country-muelle-45813240.html', 'https://www.zonaprop.com.ar/propiedades/3-ambientes-frutilla-al-500-40260227.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-43822390.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-m3-a-45483996.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-3-303-c-33361380.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-m6-a-45484001.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-43822385.html', 'https://www.zonaprop.com.ar/propiedades/lote.-av-7-lagos-al-100-40098217.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-duplex-en-el-mercado-46341773.html', 'https://www.zonaprop.com.ar/propiedades/lote.-av-7-lagos-al-100-40098199.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-7-704-n-43854075.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-puerto-la-mansa-2-amb-con-costa-44295843.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-m4-b-45483999.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-5-501-n-43854079.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-m5-a-45484000.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-3-302-c-33361382.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-loteo-tres-cerros-46431890.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-32354017.html', 'https://www.zonaprop.com.ar/propiedades/lote-vista-al-lago-con-proyecto-aprobado-14-unidades-46341772.html', 'https://www.zonaprop.com.ar/propiedades/lote.-av-7-lagos-al-100-32363945.html', 'https://www.zonaprop.com.ar/propiedades/casa-a-estrenar-en-venta-en-puerto-manzano-46341771.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-1-104-c-44024329.html', 'https://www.zonaprop.com.ar/propiedades/casa-villa-la-angostura-46065718.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-m6-b-45484002.html', 'https://www.zonaprop.com.ar/propiedades/lote-michay-44462764.html', 'https://www.zonaprop.com.ar/propiedades/4-ambientes-traful-al-500-44225016.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-5-503-c-43854071.html', 'https://www.zonaprop.com.ar/propiedades/casa-4-ambientes.-antilhue-44462757.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-32353998.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-3-301-n-33361403.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-6-605-n-43854078.html', 'https://www.zonaprop.com.ar/propiedades/casa-pto.-manzano-46065727.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-3-305-n-43171245.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-6-601-n-43907579.html', 'https://www.zonaprop.com.ar/propiedades/cabanas-3-turisticas-bahia-manzano-operativas!-46261583.html', 'https://www.zonaprop.com.ar/propiedades/lote.-av-7-lagos-al-100-32363946.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-ex-231-7-703-n-43854074.html', 'https://www.zonaprop.com.ar/propiedades/negocio.-av-arrayanes-al-200-43366739.html', 'https://www.zonaprop.com.ar/propiedades/casa-villa-la-angostura-barrio-el-once-centrica-46183536.html', 'https://www.zonaprop.com.ar/propiedades/lote-con-70-m-de-costa-en-villa-la-angostura-42094130.html', 'https://www.zonaprop.com.ar/propiedades/lote-michay-44462766.html', 'https://www.zonaprop.com.ar/propiedades/casa-4-ambientes.-boulevard-quetrihue-40098194.html', 'https://www.zonaprop.com.ar/propiedades/4-ambientes-colihue-44462761.html', 'https://www.zonaprop.com.ar/propiedades/terreno-centrico-el-mercado-villa-la-angostura-1006-46169832.html', 'https://www.zonaprop.com.ar/propiedades/casa-mas-cabana-ideal-para-vivienda-y-renta-villa-la-44606429.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-haakon.-unidad-2a-44704695.html', 'https://www.zonaprop.com.ar/propiedades/terreno-con-vista-al-lago-en-villa-la-angostura-44618121.html', 'https://www.zonaprop.com.ar/propiedades/casa-costa-de-lago-villa-correntoso-villa-la-46219781.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-barrio-puerto-nahuel-a-100-m-playa-lago-44572319.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-lote-en-venta-bahia-manzano-44280765.html', 'https://www.zonaprop.com.ar/propiedades/casa-b-paseo-del-cipres-villa-la-angostura-250-45390771.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-venta-de-3-dorm.-en-villa-la-angostura-45646148.html', 'https://www.zonaprop.com.ar/propiedades/exclusivo-lote-villa-la-angostura-c-acceso-al-lago-45219793.html', 'https://www.zonaprop.com.ar/propiedades/venta-calle-27-45943210.html', 'https://www.zonaprop.com.ar/propiedades/exclusivo-lote-villa-la-angostura-c-acceso-al-lago-45112258.html', 'https://www.zonaprop.com.ar/propiedades/casa-impecable-en-puerto-manzano-46341849.html', 'https://www.zonaprop.com.ar/propiedades/departamento-79-7-m-sup2--b.-nautico-costa-de-lago-n.-45736054.html', 'https://www.zonaprop.com.ar/propiedades/restaurante-parrilla-pleno-centro-venta-con-propiedad-46341821.html', 'https://www.zonaprop.com.ar/propiedades/lote-rododendros-vila-la-angostura-44462762.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42291519.html', 'https://www.zonaprop.com.ar/propiedades/casa-villa-la-angostura-45215576.html', 'https://www.zonaprop.com.ar/propiedades/cabana-73-m-sup2--sobre-lote-1000-m-sup2--bvd.-44842105.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-altos-del-manzano-con-planos-de-2-volumenes-46341794.html', 'https://www.zonaprop.com.ar/propiedades/hosteria-hotel-en-venta-en-villa-la-angostura-44596767.html', 'https://www.zonaprop.com.ar/propiedades/local-comercial-el-mercado-villa-la-angostura-44874794.html', 'https://www.zonaprop.com.ar/propiedades/cabana-75-m-sup2--en-villa-la-angostura-oportunidad!-46157504.html', 'https://www.zonaprop.com.ar/propiedades/casa-cabana-en-puerto-manzano-vista-parcial-lago-a-45211887.html', 'https://www.zonaprop.com.ar/propiedades/lote-244-m-sup2--con-planos-aprobados-70-m-sup2--45615984.html', 'https://www.zonaprop.com.ar/propiedades/preventa-en-pozo-oportunidad!-departamento-villa-la-44600838.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-antares-44733428.html', 'https://www.zonaprop.com.ar/propiedades/departamento-3-ambientes.-cacique-antriao-al-3900-46214032.html', 'https://www.zonaprop.com.ar/propiedades/remax-cordillera-vende-en-villa-la-angostura-46074696.html', 'https://www.zonaprop.com.ar/propiedades/venta-muelle-de-piedra-46075392.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-del-radal-al-63000-46319217.html', 'https://www.zonaprop.com.ar/propiedades/haakon.-unidad-2c-44704692.html', 'https://www.zonaprop.com.ar/propiedades/casa-villa-la-angostura-46065688.html', 'https://www.zonaprop.com.ar/propiedades/hotel-boutique-3-estrellas-impecable!-camino-al-puerto-46389897.html', 'https://www.zonaprop.com.ar/propiedades/departamento-118-5-m-sup2--b.-nautico-costa-de-lago-n.-45736052.html', 'https://www.zonaprop.com.ar/propiedades/lote-16-barrio-privado-con-acceso-a-costa-de-lago-y-46418663.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42291448.html', 'https://www.zonaprop.com.ar/propiedades/casa-90-m-sup2--lote-588-m-sup2--villa-la-angostura-46266602.html', 'https://www.zonaprop.com.ar/propiedades/venta-zorzal-c2-45943218.html', 'https://www.zonaprop.com.ar/propiedades/neg-especiales-en-venta-en-villa-la-angostura-45094670.html', 'https://www.zonaprop.com.ar/propiedades/local-comercial-centrico-en-venta-46341852.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad.-villa-la-angostura-lote-1500-m-sup2-44445547.html', 'https://www.zonaprop.com.ar/propiedades/vendo-lote-11.257-m-sup2--en-muelle-de-piedra-villa-46381275.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-villa-la-angostura-44347978.html', 'https://www.zonaprop.com.ar/propiedades/departamento-financiado-en-lomas-del-correntoso-46341838.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-lote-residencial-en-venta-2933-44279659.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-haakon.-unidad-2b-44704688.html', 'https://www.zonaprop.com.ar/propiedades/paraiso-natural-en-villa-la-angostura-46386158.html', 'https://www.zonaprop.com.ar/propiedades/lote-1736-m-sup2--villa-correntoso-villa-la-44557244.html', 'https://www.zonaprop.com.ar/propiedades/peninsula-manzano-costa-de-lago-vla-44202865.html', 'https://www.zonaprop.com.ar/propiedades/casa-muy-amplia-en-barrio-epulafquen-46341800.html', 'https://www.zonaprop.com.ar/propiedades/importante-local-comercial-gastronomico-en-pleno-46341782.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-lote-2582-m-sup2--c-vista-y-acceso-45219794.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42327122.html', 'https://www.zonaprop.com.ar/propiedades/equipo-remax-vende-casa-en-villa-la-angostura-45099656.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-45815469.html', 'https://www.zonaprop.com.ar/propiedades/preventa-en-pozo-oportunidad!-departamento-villa-la-44600840.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-4-dorm.-en-villa-la-angostura-45646153.html', 'https://www.zonaprop.com.ar/propiedades/departamento-3-ambientes.-av-7-lagos-al-100-42620631.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-duplex-en-el-mercado-46341860.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-barrio-norte-villa-la-angostura-65-m-sup2--45569942.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-l5-45943216.html', 'https://www.zonaprop.com.ar/propiedades/terreno-lote-en-manzano-chico-villa-la-angostura-1268-45952902.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44880167.html', 'https://www.zonaprop.com.ar/propiedades/departamento-3-ambientes.-cacique-antriao-al-3900-44883358.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-3-dorm.-en-puerto-manzano-villa-la-45646129.html', 'https://www.zonaprop.com.ar/propiedades/departamento-centrico-3-ambientes-con-cochera-y-46341855.html', 'https://www.zonaprop.com.ar/propiedades/imperdibles-cabanas-en-el-centro-de-villa-la-angostura-45353041.html', 'https://www.zonaprop.com.ar/propiedades/4-ambientes-osa-mayor-44964159.html', 'https://www.zonaprop.com.ar/propiedades/casa-4-ambientes.-las-frutillas-al-400-45892611.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-cauquen-al-100-46282480.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-4-dorm.-c-cochera-en-villa-la-45646172.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-120-m-sup2--en-barrio-tres-cerros-villa-la-44634840.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-2-dorm.-en-villa-la-angostura-45543930.html', 'https://www.zonaprop.com.ar/propiedades/4086-m-sup2-43143440.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-135-m-sup2--sobre-lote-de-1.000-m-sup2--en-46201677.html', 'https://www.zonaprop.com.ar/propiedades/casa-b-mallin-villa-la-angostura-80-m-sup2--lote-45592187.html', 'https://www.zonaprop.com.ar/propiedades/terreno-con-vista-al-lago-en-villa-la-angostura-44535461.html', 'https://www.zonaprop.com.ar/propiedades/preventa-en-pozo-oportunidad!-departamento-en-villa-44603396.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad-local-consultorio-en-centro-medico-44551648.html', 'https://www.zonaprop.com.ar/propiedades/7-ambientes-o-mas-los-pioneros-355-32029944.html', 'https://www.zonaprop.com.ar/propiedades/complejo-de-cabanas-y-departamentos-primer-nivel-46389909.html', 'https://www.zonaprop.com.ar/propiedades/local-comercial-58-28-m-sup2--galeria-sobre-av-46240438.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-l3-45943214.html', 'https://www.zonaprop.com.ar/propiedades/departamento-3-ambientes.-las-retamas-al-300-45886739.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-casa-barrio-cerrado-rucahue-200-45472006.html', 'https://www.zonaprop.com.ar/propiedades/departamento-79-7-m-sup2--b.-nautico-costa-de-lago-n.-45735678.html', 'https://www.zonaprop.com.ar/propiedades/preventa-en-pozo-oportunidad!-departamento-villa-la-44600957.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-70-m-sup2--sobre-lote-de-550-m-sup2--en-villa-45175415.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad!-ideal-p-loteo-o-emprendimiento-2-lotes-46156631.html', 'https://www.zonaprop.com.ar/propiedades/lote-2278-m-sup2--a-200-m-de-playa-lago-n.-huapi-44574326.html', 'https://www.zonaprop.com.ar/propiedades/terreno-centrico-el-mercado-villa-la-angostura-2384-46290990.html', 'https://www.zonaprop.com.ar/propiedades/lote-ruta-231-44986473.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44880212.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44883323.html', 'https://www.zonaprop.com.ar/propiedades/complejo-de-5-cabanas-3-vivienda-principal.-43784449.html', 'https://www.zonaprop.com.ar/propiedades/lote-con-planos-aprobados-6-cabanas-70-m-sup2--zona-44502691.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-reservada-haakon.-unidad-2d-44704684.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-villa-la-angostura-excelente-vista-o-45647005.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44879791.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-4-dorm.-c-cochera-en-villa-la-45646131.html', 'https://www.zonaprop.com.ar/propiedades/terreno-de-967-m-sup2--en-villa-la-angostura-faldeo-45409632.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-reservada-haakon-unidad-pb-e-46006482.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42291451.html', 'https://www.zonaprop.com.ar/propiedades/exclusivo-lote-villa-la-angostura-c-acceso-al-lago-45219786.html', 'https://www.zonaprop.com.ar/propiedades/fondo-de-comercio-en-av-principal-villa-la-angostura-46182621.html', 'https://www.zonaprop.com.ar/propiedades/casa-vista-al-lago-barrio-arauco-villa-la-angostura-45506340.html', 'https://www.zonaprop.com.ar/propiedades/departamento-centrico-a-estrenar-3-ambientes-46341834.html', 'https://www.zonaprop.com.ar/propiedades/haakon.-unidad-pb-c-46006450.html', 'https://www.zonaprop.com.ar/propiedades/cabana-en-villa-la-angostura-45671567.html', 'https://www.zonaprop.com.ar/propiedades/departamento-monoambiente.-el-mercado-46142628.html', 'https://www.zonaprop.com.ar/propiedades/equipo-remax-cordillera-vende-en-la-angostura-46011426.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-l2-45943213.html', 'https://www.zonaprop.com.ar/propiedades/casa-4-ambientes.-chos-malal-al-400-46295568.html', 'https://www.zonaprop.com.ar/propiedades/lote-bellisimo-en-cumelen-country-club-con-vista-al-46341846.html', 'https://www.zonaprop.com.ar/propiedades/casa-gran-categoria-con-vista-franca-al-lago-nahuel-46341777.html', 'https://www.zonaprop.com.ar/propiedades/espectacular-hosteria-3-en-venta-villa-la-angostura-42857957.html', 'https://www.zonaprop.com.ar/propiedades/terreno-de-8900-m-sup2--en-venta-villa-la-angostura-45126968.html', 'https://www.zonaprop.com.ar/propiedades/3-ambientes-traful-44848037.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-venta-de-2230-m-sup2--ubicado-en-villa-la-45646173.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-venta-de-2230-m-sup2--ubicado-en-villa-la-45646174.html', 'https://www.zonaprop.com.ar/propiedades/muelle-de-piedra-un-paraiso!-33318655.html', 'https://www.zonaprop.com.ar/propiedades/casa-4-ambientes.-lacar-al-200-45880300.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-venta-de-1-dorm.-en-villa-la-angostura-45646125.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-5-dorm.-en-villa-la-angostura-45646176.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-haakon.-unidad-1b-44704725.html', 'https://www.zonaprop.com.ar/propiedades/lote-de-3.594-99-m-sup2--en-barrio-parque-arauco-45802876.html', 'https://www.zonaprop.com.ar/propiedades/cabana-70-m-sup2--sobre-lote-260-m-sup2--con-barrio-44603398.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-venta-de-2848-m-sup2--ubicado-en-villa-la-45554924.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-puerto-manzano-46341854.html', 'https://www.zonaprop.com.ar/propiedades/terreno-3.131-m-sup2--en-villa-la-angostura-b-46239845.html', 'https://www.zonaprop.com.ar/propiedades/departamento-financiado-en-lomas-del-correntoso-46341837.html', 'https://www.zonaprop.com.ar/propiedades/departamento-villa-la-angostura-45970673.html', 'https://www.zonaprop.com.ar/propiedades/casa-bahia-manzano-villa-la-angostura-85-m-sup2-45555213.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-venta-de-0-m-sup2--ubicado-en-villa-la-45543946.html', 'https://www.zonaprop.com.ar/propiedades/terreno-de-9.959-m-sup2--en-lomas-del-correntoso-46000396.html', 'https://www.zonaprop.com.ar/propiedades/venta-huemul-ruta-40-46135750.html', 'https://www.zonaprop.com.ar/propiedades/departamento-financiado-en-lomas-del-correntoso-46341840.html', 'https://www.zonaprop.com.ar/propiedades/susana-aravena-propiedades-ds-vende-galeria-comercial-46200810.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-2-dorm.-c-cochera-en-villa-la-45646128.html', 'https://www.zonaprop.com.ar/propiedades/venta-miradores-del-conde-l5-46352876.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-faldeo-del-bayo-46341845.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-ph-1.067-m-sup2--loteo-selvana-villa-la-44915006.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-local-de-27-m-sup2--a-estrenar-45951401.html', 'https://www.zonaprop.com.ar/propiedades/departamento-centrico-a-estrenar-3-ambientes-46341833.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42290520.html', 'https://www.zonaprop.com.ar/propiedades/departamento-oportunidad!-en-pb-con-galeria-en-el-46341842.html', 'https://www.zonaprop.com.ar/propiedades/casa-5-ambientes.-michay-al-200-44704734.html', 'https://www.zonaprop.com.ar/propiedades/4-departamentos-sobre-lote-500-m-sup2--exc-ubicac.-46239867.html', 'https://www.zonaprop.com.ar/propiedades/venta-hortensias-c2-46285820.html', 'https://www.zonaprop.com.ar/propiedades/cabana-villa-la-angostura-45323744.html', 'https://www.zonaprop.com.ar/propiedades/susana-aravena-propiedades-ds-vende-exclusiva-46336823.html', 'https://www.zonaprop.com.ar/propiedades/lote-6.000-m-sup2--faldeo-del-bayo-villa-la-angostura-44511095.html', 'https://www.zonaprop.com.ar/propiedades/casa-211-m-sup2--en-b.-nautico-costa-de-lago-n.-huapi-45728902.html', 'https://www.zonaprop.com.ar/propiedades/venta-hortensias-c1-46285819.html', 'https://www.zonaprop.com.ar/propiedades/fraccion-sobre-ruta-con-impresionante-vista-al-lago-y-46341826.html', 'https://www.zonaprop.com.ar/propiedades/venta-impecable-casa-en-exclusivo-barrio-lomas-del-44747345.html', 'https://www.zonaprop.com.ar/propiedades/lotes-en-block-barrio-el-once-46341818.html', 'https://www.zonaprop.com.ar/propiedades/terreno-villa-la-angostura-46274004.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-135-m-sup2--con-2-lofts-turisticos-lote-de-45111626.html', 'https://www.zonaprop.com.ar/propiedades/cabana-de-63-m-sup2--venta-en-pozo-villa-la-45251693.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad!-ideal-p-emprendimiento-2-lotes-46128167.html', 'https://www.zonaprop.com.ar/propiedades/lote-terreno-de-1.500-m-sup2--en-villa-la-angostura-45736023.html', 'https://www.zonaprop.com.ar/propiedades/venta-casa-barrio-tres-cerros-villa-la-angostura-79-46079679.html', 'https://www.zonaprop.com.ar/propiedades/equipo-remax-vende-fraccion-en-villa-la-angostura-45487888.html', 'https://www.zonaprop.com.ar/propiedades/departamento-financiado-en-lomas-del-correntoso-46341841.html', 'https://www.zonaprop.com.ar/propiedades/terreno-de-10.588-m-sup2--en-el-faldeo-del-bayo-villa-46000621.html', 'https://www.zonaprop.com.ar/propiedades/terreno-en-muelle-de-piedra-46386206.html', 'https://www.zonaprop.com.ar/propiedades/casa-b-las-piedritas-villa-la-angostura-45-45713642.html', 'https://www.zonaprop.com.ar/propiedades/lote-14-barrio-privado-con-acceso-a-costa-de-lago-y-46418874.html', 'https://www.zonaprop.com.ar/propiedades/propiedad-reservada-departamento-2-ambientes.-44880179.html', 'https://www.zonaprop.com.ar/propiedades/casa-5-ambientes.-paimun-44734208.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-ph-moderno-y-luminoso-en-barrio-44910527.html', 'https://www.zonaprop.com.ar/propiedades/terreno-de-908-m-sup2--en-bahia-manzano-villa-la-46204180.html', 'https://www.zonaprop.com.ar/propiedades/lote-peninsula-manzano-para-desarrollo-5488-m-sup2-45219441.html', 'https://www.zonaprop.com.ar/propiedades/remax-cordillera-vende-lote-en-villa-la-angostura-45961056.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-reservada-haakon.-unidad-1d-44704708.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-lote-en-venta-puerto-manzano-44280400.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44879845.html', 'https://www.zonaprop.com.ar/propiedades/local-comercial-en-galeria-sobre-av-arrayanes-46341830.html', 'https://www.zonaprop.com.ar/propiedades/departamento-99.8-m-sup2--b.-nautico-costa-de-lago-n.-45732512.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-4-dorm.-c-cochera-en-villa-la-45646127.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-zorzal-45688233.html', 'https://www.zonaprop.com.ar/propiedades/casa-b-privado-rucahue-las-balsas-villa-la-45580595.html', 'https://www.zonaprop.com.ar/propiedades/lotes-miradores-del-bayo-vista-al-lago-46341825.html', 'https://www.zonaprop.com.ar/propiedades/lote-244-m-sup2--con-planos-aprobados-70-m-sup2--45626298.html', 'https://www.zonaprop.com.ar/propiedades/departamento-3-ambientes.-cacique-antriao-al-3900-45817921.html', 'https://www.zonaprop.com.ar/propiedades/venta-miradores-del-conde-l3-46352874.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-275-m-sup2--sobre-terreno-de-1.190-m-sup2--en-45175373.html', 'https://www.zonaprop.com.ar/propiedades/lote.-calfuco-al-200-45914440.html', 'https://www.zonaprop.com.ar/propiedades/lote.-calfuco-al-viii00-45930993.html', 'https://www.zonaprop.com.ar/propiedades/lote-3-barrio-privado-con-acceso-a-costa-de-lago-y-46418871.html', 'https://www.zonaprop.com.ar/propiedades/preventa-oportunidad!-departamento-en-el-mercado-44600834.html', 'https://www.zonaprop.com.ar/propiedades/lote-2278-m-sup2--a-200-m-de-playa-lago-n.-huapi-44574326.html', 'https://www.zonaprop.com.ar/propiedades/espectacular-fraccion-vista-lago-nahuel-huapi-46341853.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-120-m-sup2--en-barrio-tres-cerros-villa-la-44634840.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-4-dorm.-en-villa-la-angostura-45646153.html', 'https://www.zonaprop.com.ar/propiedades/preventa-en-pozo-departamento-en-el-mercado-villa-44603397.html', 'https://www.zonaprop.com.ar/propiedades/lote-de-310-m-sup2--con-planos-aprobados-villa-la-46381169.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-venta-de-1000-m-sup2--ubicado-en-villa-la-45543928.html', 'https://www.zonaprop.com.ar/propiedades/fondo-de-comercio-empresa-de-viajes-y-turismo-en-villa-45032454.html', 'https://www.zonaprop.com.ar/propiedades/casa-centrica-villa-la-angostura-85-m-sup2--cub-lote-46418806.html', 'https://www.zonaprop.com.ar/propiedades/lote-terreno-de-2.885-m-sup2--en-villa-la-angostura-45736024.html', 'https://www.zonaprop.com.ar/propiedades/peninsula-manzano-costa-de-lago-vla-44202865.html', 'https://www.zonaprop.com.ar/propiedades/departamentos-financiados-en-construccion-en-el-centro-46341848.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad!-lote-c-planos-p-cabana-85-m-sup2--zona-44502690.html', 'https://www.zonaprop.com.ar/propiedades/terreno-en-venta-de-nanm-sup2--ubicado-en-villa-la-45646121.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-local-de-27-m-sup2--a-estrenar-45951401.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-ph-2-plantas-en-barrio-norte-oportunidad!-46341804.html', 'https://www.zonaprop.com.ar/propiedades/venta-chucao-62-45943208.html', 'https://www.zonaprop.com.ar/propiedades/terreno-con-vista-al-lago-en-villa-la-angostura-44535461.html', 'https://www.zonaprop.com.ar/propiedades/casa-b-privado-rucahue-las-balsas-villa-la-45580595.html', 'https://www.zonaprop.com.ar/propiedades/terreno-de-4650-m-sup2--faldeo-del-bayo-villa-la-44511098.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-faldeo-del-bayo-46341845.html', 'https://www.zonaprop.com.ar/propiedades/cabanas-en-villa-la-angostura-neuquen-44506092.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-lote-en-venta-bahia-manzano-44280765.html', 'https://www.zonaprop.com.ar/propiedades/terreno-comercial-residenc-villa-la-angostura-1001.34-46239827.html', 'https://www.zonaprop.com.ar/propiedades/remax-cordillera-vende-lote-en-villa-la-angostura-45828771.html', 'https://www.zonaprop.com.ar/propiedades/terreno-900-m-sup2--en-villa-la-angostura-faldeo-del-45402541.html', 'https://www.zonaprop.com.ar/propiedades/equipo-remax-cordillera-vende-en-la-angostura-46011426.html', 'https://www.zonaprop.com.ar/propiedades/venta-miradores-del-conde-l3-46352874.html', 'https://www.zonaprop.com.ar/propiedades/preventa-en-pozo-oportunidad!-departamento-villa-la-44600840.html', 'https://www.zonaprop.com.ar/propiedades/departamento-118-5-m-sup2--b.-nautico-costa-de-lago-n.-45739552.html', 'https://www.zonaprop.com.ar/propiedades/local-comercial-en-galeria-sobre-av-arrayanes-46341830.html', 'https://www.zonaprop.com.ar/propiedades/haakon.-unidad-pb-c-46006450.html', 'https://www.zonaprop.com.ar/propiedades/lote-peninsula-manzano-para-desarrollo-5488-m-sup2-45219441.html', 'https://www.zonaprop.com.ar/propiedades/lotes-miradores-del-bayo-vista-al-lago-46341825.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44879791.html', 'https://www.zonaprop.com.ar/propiedades/fondo-de-comercio-gastronomico-el-cruce-en-villa-la-44865659.html', 'https://www.zonaprop.com.ar/propiedades/terreno-3.131-m-sup2--en-villa-la-angostura-b-46239845.html', 'https://www.zonaprop.com.ar/propiedades/departamento-de-17-m-sup2--en-el-mercado-villa-la-45952901.html', 'https://www.zonaprop.com.ar/propiedades/casa-b-paseo-del-cipres-villa-la-angostura-250-45390771.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-haakon.-unidad-2a-44704695.html', 'https://www.zonaprop.com.ar/propiedades/departamento-79-7-m-sup2--b.-nautico-costa-de-lago-n.-45736054.html', 'https://www.zonaprop.com.ar/propiedades/venta-miradores-del-conde-l1-46352872.html', 'https://www.zonaprop.com.ar/propiedades/venta-depto-01-03-uf102-en-pozo-costa-de-lago-2-amb-46090792.html', 'https://www.zonaprop.com.ar/propiedades/terreno-centrico-el-mercado-villa-la-angostura-3216-42-46291053.html', 'https://www.zonaprop.com.ar/propiedades/duplex-en-venta-de-2-dorm.-en-villa-la-angostura-45646124.html', 'https://www.zonaprop.com.ar/propiedades/3-ambientes-traful-44848037.html', 'https://www.zonaprop.com.ar/propiedades/duplex-en-venta-de-2-dorm.-en-villa-la-angostura-45646139.html', 'https://www.zonaprop.com.ar/propiedades/exclusivo-lote-en-ph-de-2454-m-sup2--barrio-45312845.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-barrio-privado-las-lomas-permuto-por-depto-en-45655535.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-villa-la-angostura-44347978.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-l3-45943214.html', 'https://www.zonaprop.com.ar/propiedades/4-ambientes-osa-mayor-44964159.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42291447.html', 'https://www.zonaprop.com.ar/propiedades/terreno-3.131-m-sup2--en-villa-la-angostura-b-46239845.html', 'https://www.zonaprop.com.ar/propiedades/casa-mas-departamento-en-puerto-manzano-46341805.html', 'https://www.zonaprop.com.ar/propiedades/preventa-en-pozo-oportunidad!-departamento-en-villa-44603396.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-135-m-sup2--con-2-lofts-turisticos-lote-de-45111626.html', 'https://www.zonaprop.com.ar/propiedades/casa-villa-la-angostura-45215576.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-45817823.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-del-radal-al-63000-46319217.html', 'https://www.zonaprop.com.ar/propiedades/lote-244-m-sup2--con-planos-aprobados-70-m-sup2--45615984.html', 'https://www.zonaprop.com.ar/propiedades/lote-de-7.194-m-sup2--con-vista-al-lago-en-barrio-45849107.html', 'https://www.zonaprop.com.ar/propiedades/terreno-centrico-comercial-villa-la-angostura-3042-75-46291025.html', 'https://www.zonaprop.com.ar/propiedades/casa-211-m-sup2--en-b.-nautico-costa-de-lago-n.-huapi-45727607.html', 'https://www.zonaprop.com.ar/propiedades/exclusivo-lote-villa-la-angostura-c-acceso-al-lago-45219793.html', 'https://www.zonaprop.com.ar/propiedades/hotel-boutique-3-estrellas-impecable!-camino-al-puerto-46389897.html', 'https://www.zonaprop.com.ar/propiedades/terreno-de-4650-m-sup2--faldeo-del-bayo-villa-la-44511098.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-venta-de-m-sup2--ubicado-en-villa-la-angostura-45646122.html', 'https://www.zonaprop.com.ar/propiedades/departamento-118-5-m-sup2--b.-nautico-costa-de-lago-n.-45736052.html', 'https://www.zonaprop.com.ar/propiedades/equipo-remax-cordillera-vende-en-la-angostura-46011426.html', 'https://www.zonaprop.com.ar/propiedades/terreno-en-venta-de-nanm-sup2--ubicado-en-villa-la-45646121.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-haakon.-unidad-1b-44704725.html', 'https://www.zonaprop.com.ar/propiedades/venta-muy-buena-casa.-villa-la-angostura-46156969.html', 'https://www.zonaprop.com.ar/propiedades/casa-5-ambientes.-paimun-44734208.html', 'https://www.zonaprop.com.ar/propiedades/venta-huemul-ruta-40-45943204.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-villa-la-angostura-con-vista-al-lago-playa-45655534.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-ph-moderno-y-luminoso-en-barrio-44910527.html', 'https://www.zonaprop.com.ar/propiedades/terreno-con-vista-al-lago-en-villa-la-angostura-44618121.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-haakon.-unidad-pb-b-46006425.html', 'https://www.zonaprop.com.ar/propiedades/equipo-remax-vende-casa-en-villa-la-angostura-45099656.html', 'https://www.zonaprop.com.ar/propiedades/terreno-en-muelle-de-piedra-46386206.html', 'https://www.zonaprop.com.ar/propiedades/restaurada-y-ampliada-con-vista-a-los-cerros-45968236.html', 'https://www.zonaprop.com.ar/propiedades/apart-hotel-16-hab.-3-43562916.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42327122.html', 'https://www.zonaprop.com.ar/propiedades/lote-bellisimo-en-cumelen-country-club-con-vista-al-46341846.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-lote-2582-m-sup2--c-vista-y-acceso-45219794.html', 'https://www.zonaprop.com.ar/propiedades/terreno-con-vista-al-lago-nahuel-huapi-a-2-km-del-45410229.html', 'https://www.zonaprop.com.ar/propiedades/haakon.-unidad-1c-44704712.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-4-dorm.-en-villa-la-angostura-45646153.html', 'https://www.zonaprop.com.ar/propiedades/lote-fraccion-sobre-ruta-40-vista-al-lago-46341824.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44880187.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-pegaso-45789394.html', 'https://www.zonaprop.com.ar/propiedades/lote-7-barrio-privado-con-acceso-a-costa-de-lago-y-46418872.html', 'https://www.zonaprop.com.ar/propiedades/venta-zorzal-c2-45943218.html', 'https://www.zonaprop.com.ar/propiedades/hosteria-hotel-en-venta-en-villa-la-angostura-44596767.html', 'https://www.zonaprop.com.ar/propiedades/haakon.-unidad-pb-d-46006473.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-ph-2-plantas-en-barrio-norte-oportunidad!-46341804.html', 'https://www.zonaprop.com.ar/propiedades/venta-depto-02-05-uf204-en-pozo-costa-de-lago-2-amb-46098453.html', 'https://www.zonaprop.com.ar/propiedades/casa-a-estrenar-110-m-sup2--faldeos-del-bayo-villa-44515947.html', 'https://www.zonaprop.com.ar/propiedades/4-casas-en-venta-en-un-lote-de-1.420-m-sup2--en-barrio-46291050.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad!-lote-c-planos-p-cabana-85-m-sup2--zona-44502690.html', 'https://www.zonaprop.com.ar/propiedades/casa-a-estrenar-en-villa-la-angostura-excelente-45704761.html', 'https://www.zonaprop.com.ar/propiedades/casa-2-dorm-90-m-villa-la-angostura-cerca-escuelas-44874795.html', 'https://www.zonaprop.com.ar/propiedades/equipo-remax-cordillera-vende-cabana-en-vla-46160762.html', 'https://www.zonaprop.com.ar/propiedades/lote-3-barrio-privado-con-acceso-a-costa-de-lago-y-46418871.html', 'https://www.zonaprop.com.ar/propiedades/preventa-en-pozo-oportunidad!-departamento-villa-la-44600840.html', 'https://www.zonaprop.com.ar/propiedades/cabanas-3-ambientes-en-villa-la-angostura-45827261.html', 'https://www.zonaprop.com.ar/propiedades/casa-cabana-100-m-sup2--a-estrenar-b-las-balsas-45531991.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42290520.html', 'https://www.zonaprop.com.ar/propiedades/venta-casa-barrio-tres-cerros-villa-la-angostura-79-46079679.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-venta-de-0-m-sup2--ubicado-en-villa-la-45543946.html', 'https://www.zonaprop.com.ar/propiedades/lote.-el-mercado-al-600-45941563.html', 'https://www.zonaprop.com.ar/propiedades/local.-av-arrayanes-al-600-46013393.html', 'https://www.zonaprop.com.ar/propiedades/departamento-3-ambientes.-las-retamas-al-300-45886739.html', 'https://www.zonaprop.com.ar/propiedades/lote-de-700-m-sup2--con-vista-al-lago-en-villa-la-46381295.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-reservada-haakon.-unidad-2d-44704684.html', 'https://www.zonaprop.com.ar/propiedades/lote-de-310-m-sup2--con-planos-aprobados-villa-la-46381169.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-135-m-sup2--sobre-lote-de-1.000-m-sup2--en-46201677.html', 'https://www.zonaprop.com.ar/propiedades/casa-b-privado-rucahue-las-balsas-villa-la-45580595.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42291454.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42290118.html', 'https://www.zonaprop.com.ar/propiedades/exclusivo-lote-2.575-m-sup2--c-vista-y-acceso-al-lago-45219792.html', 'https://www.zonaprop.com.ar/propiedades/casa-a-estrenar-en-venta-en-puerto-manzano-46341820.html', 'https://www.zonaprop.com.ar/propiedades/complejo-de-5-cabanas-3-vivienda-principal.-43784449.html', 'https://www.zonaprop.com.ar/propiedades/depto-costa-lago-desarrollo-inmobiliario-en-pozo-44469562.html', 'https://www.zonaprop.com.ar/propiedades/departamento-financiado-en-lomas-del-correntoso-46341839.html', 'https://www.zonaprop.com.ar/propiedades/casa-centrica-villa-la-angostura-85-m-sup2--cub-lote-46418806.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-l4-45943215.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-3-dorm.-en-puerto-manzano-villa-la-45646129.html', 'https://www.zonaprop.com.ar/propiedades/departamento-financiado-en-lomas-del-correntoso-46341835.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-duplex-en-el-mercado-46341860.html', 'https://www.zonaprop.com.ar/propiedades/lote-6.000-m-sup2--faldeo-del-bayo-villa-la-angostura-44511095.html', 'https://www.zonaprop.com.ar/propiedades/muelle-de-piedra-lotes-43657515.html', 'https://www.zonaprop.com.ar/propiedades/terreno-con-vista-al-lago-en-villa-la-angostura-44535461.html', 'https://www.zonaprop.com.ar/propiedades/casa-4-ambientes.-lacar-al-200-45880300.html', 'https://www.zonaprop.com.ar/propiedades/remax-cordillera-vende-en-villa-la-angostura-46074696.html', 'https://www.zonaprop.com.ar/propiedades/susana-aravena-propiedades-ds-vende-galeria-comercial-46200810.html', 'https://www.zonaprop.com.ar/propiedades/7-ambientes-o-mas-los-pioneros-355-32029944.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44879791.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-4-dorm.-c-cochera-en-villa-la-45646130.html', 'https://www.zonaprop.com.ar/propiedades/lote-1736-m-sup2--villa-correntoso-villa-la-44557244.html', 'https://www.zonaprop.com.ar/propiedades/departamento-99.8-m-sup2--b.-nautico-costa-de-lago-n.-45732512.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-bahia-manzano-lote-en-venta-con-44280788.html', 'https://www.zonaprop.com.ar/propiedades/cabanas-de-alquiler-turistico-en-puerto-manzano-46406341.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44883338.html', 'https://www.zonaprop.com.ar/propiedades/departamento-monoambiente.-el-mercado-46142628.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-275-m-sup2--sobre-terreno-de-1.190-m-sup2--en-45175373.html', 'https://www.zonaprop.com.ar/propiedades/muelle-de-piedra-un-paraiso!-33318655.html', 'https://www.zonaprop.com.ar/propiedades/haakon.-unidad-pb-c-46006450.html', 'https://www.zonaprop.com.ar/propiedades/casa-exc-ubicacion-centrica-villa-la-angostura-vistas-45694385.html', 'https://www.zonaprop.com.ar/propiedades/casas-3-cabanas-en-el-centro-de-villa-la-46277981.html', 'https://www.zonaprop.com.ar/propiedades/cabana-73-m-sup2--sobre-lote-1000-m-sup2--bvd.-44842105.html', 'https://www.zonaprop.com.ar/propiedades/el-mercado-lote-comercial-46341789.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-reservada-haakon.-unidad-1d-44704708.html', 'https://www.zonaprop.com.ar/propiedades/lote-en-venta-de-2230-m-sup2--ubicado-en-villa-la-45646173.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-suspendida-haakon.-unidad-1a-44704728.html', 'https://www.zonaprop.com.ar/propiedades/lote-1496-m-sup2--b-calfuco-villa-la-angostura-44630536.html', 'https://www.zonaprop.com.ar/propiedades/preventa-oportunidad-departamento-en-el-mercado-44598271.html', 'https://www.zonaprop.com.ar/propiedades/lote-con-planos-aprobados-6-cabanas-70-m-sup2--zona-44502691.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-3-dorm.-en-villa-la-angostura-45543945.html', 'https://www.zonaprop.com.ar/propiedades/casa-226-m-sup2--en-b.-nautico-costa-de-lago-n.-huapi-45728908.html', 'https://www.zonaprop.com.ar/propiedades/casa-3-ambientes.-antares-44733428.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-lote-en-venta-puerto-manzano-44280400.html', 'https://www.zonaprop.com.ar/propiedades/venta-ruta-40-l2-45943213.html', 'https://www.zonaprop.com.ar/propiedades/casa-impecable-en-puerto-manzano-46341849.html', 'https://www.zonaprop.com.ar/propiedades/lote-centrico-comercial-46341788.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-4-dorm.-c-cochera-en-villa-la-45646126.html', 'https://www.zonaprop.com.ar/propiedades/lote-ruta-231-44978887.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad!-ideal-p-emprendimiento-2-lotes-46128167.html', 'https://www.zonaprop.com.ar/propiedades/depto-centrico-en-galeria-comercial-sobre-av-principal-44925470.html', 'https://www.zonaprop.com.ar/propiedades/lote.-calfuco-al-200-45914440.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44880227.html', 'https://www.zonaprop.com.ar/propiedades/casa-mas-cabana-ideal-para-vivienda-y-renta-villa-la-44606429.html', 'https://www.zonaprop.com.ar/propiedades/venta-miradores-del-conde-l5-46352876.html', 'https://www.zonaprop.com.ar/propiedades/local-comercial-el-mercado-villa-la-angostura-44874794.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-44879845.html', 'https://www.zonaprop.com.ar/propiedades/villa-la-angostura-casa-barrio-cerrado-rucahue-200-45472006.html', 'https://www.zonaprop.com.ar/propiedades/fondo-de-comercio-tienda-de-ropa-santa-ropa-en-villa-44854114.html', 'https://www.zonaprop.com.ar/propiedades/departamento-3-ambientes.-av-7-lagos-al-100-42620631.html', 'https://www.zonaprop.com.ar/propiedades/casa-cabana-en-puerto-manzano-vista-parcial-lago-a-45211887.html', 'https://www.zonaprop.com.ar/propiedades/oportunidad!-ideal-p-loteo-o-emprendimiento-2-lotes-46156631.html', 'https://www.zonaprop.com.ar/propiedades/-propiedad-reservada-haakon-unidad-pb-e-46006482.html', 'https://www.zonaprop.com.ar/propiedades/equipo-remax-vende-fraccion-en-villa-la-angostura-45487888.html', 'https://www.zonaprop.com.ar/propiedades/terreno-residencial-comercial-villa-la-angostura-46292861.html', 'https://www.zonaprop.com.ar/propiedades/casa-de-120-m-sup2--en-barrio-tres-cerros-villa-la-44634840.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-barrio-puerto-nahuel-a-100-m-playa-lago-44572319.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-venta-de-5-dorm.-en-villa-la-angostura-45646176.html', 'https://www.zonaprop.com.ar/propiedades/lote.-calfuco-al-viii00-45930993.html', 'https://www.zonaprop.com.ar/propiedades/local-de-22.5-m-sup2--a-estrenar-45951396.html', 'https://www.zonaprop.com.ar/propiedades/casa-en-puerto-manzano-46341854.html', 'https://www.zonaprop.com.ar/propiedades/complejo-epulafquen-villa-la-angostura-42291535.html', 'https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes.-cacique-antriao-al-3900-45815469.html', 'https://www.zonaprop.com.ar/propiedades/lote-de-3.594-99-m-sup2--en-barrio-parque-arauco-45802876.html', 'https://www.zonaprop.com.ar/propiedades/lote-espectacular-primera-linea-de-playa-costa-lago-46341831.html', 'https://www.zonaprop.com.ar/propiedades/venta-hortensias-c2-46285820.html', 'https://www.zonaprop.com.ar/propiedades/terreno-centrico-el-mercado-villa-la-angostura-1006-46169832.html', 'https://www.zonaprop.com.ar/propiedades/lote-rododendros-vila-la-angostura-44462762.html', 'https://www.zonaprop.com.ar/propiedades/propiedad-reservada-departamento-2-ambientes.-44880179.html', 'https://www.zonaprop.com.ar/propiedades/excelente-lote-de-1.476-m-sup2--en-puerto-manzano-46157182.html', 'https://www.zonaprop.com.ar/propiedades/departamento-en-venta-en-villa-la-angostura-46281779.html', 'https://www.zonaprop.com.ar/propiedades/casa-2-cabanas-turisticas-en-villa-la-angostura-46336045.html']

if __name__ == '__main__':
	#Scrappeo de muchos links
	zonaPropScrapper = ZonaPropScrapper() #'villa la angostura', tipoIntercambio = 'Venta', tipoPropiedad = 'Ambos')
	zonaPropScrapper.scrapeLinkList(linkList)

	#Testeo Individual
	#zonaPropScrapper = ZonaPropScrapper()
	#zonaPropScrapper.scrapeSingleLink(textLink)

	#print(zonaPropScrapper.propertyDict)


import requests
from bs4 import BeautifulSoup
import os
from pandas import DataFrame, ExcelWriter
from selenium import webdriver
import time

#BeautifulSoup no funciona con zonaprop. Usar selenium
#Usar selenium funciona para localizar elementos. Y con source selenium y bs4?

browser = webdriver.Chrome()	
browser.get('https://www.zonaprop.com.ar/propiedades/departamento-de-cuatro-ambientes-en-san-isidro-46085977.html')
time.sleep(5)


#get_div = browser.find_elements_by_class_name('title-type-sup')

#for i in get_div:
#	print(i.get_attribute('innerHTML'))

source = browser.page_source
soup = BeautifulSoup(source, 'html.parser')

print(soup.find_all('h2', class_ = 'title-type-sup'))

browser.quit()
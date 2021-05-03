import openpyxl
import shelve
from pandas import DataFrame, ExcelWriter


shelveF = shelve.open('.\\Shelve Data\\dwadaDict')
propertyDict = shelveF['dwadaDict']
shelveF.close()

myDF = DataFrame(propertyDict)
writer = ExcelWriter('..\\..\\Excel Files\\AirBnB\\test.xlsx')
myDF.to_excel(writer)
writer.save()


#wb.save('..\\..\\Excel Files\\AirBnB\\test.xlsx')



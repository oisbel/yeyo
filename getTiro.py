# coding: utf-8

from lxml import html
import requests

from database import Base, Tiro
from sqlalchemy import create_engine, asc, desc, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

import dateutil.parser as dparser
from datetime import datetime, timedelta

# Connect to Database and create database session
engine = create_engine('sqlite:///yeyo.db')
# engine = create_engine('postgresql://yeyo:Vryyo_18@localhost/yeyo')
Base.metadata.bind = engine
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

def getLastTiro():
	""" Devuelve el ultimo tiro de la base de datos"""
	session = Session()
	try:
	    tiro = session.query(Tiro).order_by(Tiro.id.desc()).limit(1).one()
	except:
		session.close()
		return None
	session.close()
	return tiro

def new_tiro(tiroStr):
	""" Agrega un tiro a la base de datos"""
	session = Session()
	tiro = Tiro(fecha=tiroStr[:10], hora=tiroStr[11:12], tiro=tiroStr[13:22])
	session.add(tiro)
	session.commit()

def scraping(url):
	""" Devuelve el html de la pagina url"""
	page = requests.get(url)
	tree = html.fromstring(page.content)
	return tree	

def getXpath(tree, xpath):
	""" Recorre el arbol del html tree y recupera la lista de elementos dentro de xpath"""
	result = tree.xpath(xpath)
	s = '-'
	return s.join(result)

def main():
	tiro = getLastTiro()
	#print(tiro.fecha)
	if tiro is None:
		return
	lastDate = datetime.strptime(tiro.fecha,"%d/%m/%Y")
	#print("Ultimo tiro: " + tiro.fecha + '/' + tiro.hora + '-' + tiro.tiro + '->' + str(tiro.id))

	treePick3 = scraping('https://www.flalottery.com/pick3')
	treePick4 = scraping('https://www.flalottery.com/pick4')
	if tiro.hora == 'N':
		# descargar tiro de dia proximo dia
		nextDay = lastDate + timedelta(days=1)
		try:
			fechaPick3 = getXpath(treePick3, '//*[@id="gameContentLeft"]/div[1]/p[2]/text()') #  Thursday, April 9, 2020
			datePick3 = dparser.parse(fechaPick3, fuzzy=True)
			#print(datePick3.strftime("%d/%m/%Y"))

			fechaPick4 = getXpath(treePick4, '//*[@id="gameContentLeft"]/div[1]/p[2]/text()')
			datePick4 = dparser.parse(fechaPick4, fuzzy=True)
			#print(datePick4.strftime("%d/%m/%Y"))
		except Exception as e:
			raise e
		
		# Verificar que sea el tiro de dia del dia siguiente
		sameday = datePick3 == datePick4 == nextDay
		#print(sameday)
		if not sameday:
			#print('Todavia no se ha actualizado')
			return

		pick3 = getXpath(treePick3, '//*[@id="gameContentLeft"]/div[1]/div[2]/p[1]/span[@class="balls"]/text()') # 0-6-1
		#print(pick3)
		pick4 = getXpath(treePick4, '//*[@id="gameContentLeft"]/div[1]/div[2]/p[1]/span[@class="balls"]/text()') # 4-2-3-8
		#print(pick4)

		# Agregar tiro
		pick3 = pick3.replace('-','')
		pick4 = pick4.replace('-','')
		pick4 = pick4[:2] +'-'+ pick4[2:4]
		newTiro = nextDay.strftime("%d/%m/%Y") + '/D-' + pick3 + '-' + pick4

	else:
		#descargar tiro de noche mismo dia
		try:
			fechaPick3 = getXpath(treePick3, '//*[@id="gameContentLeft"]/div[2]/p[2]/text()')
			datePick3 = dparser.parse(fechaPick3, fuzzy=True)
			#print(datePick3.strftime("%d/%m/%Y"))

			fechaPick4 = getXpath(treePick4, '//*[@id="gameContentLeft"]/div[2]/p[2]/text()')
			datePick4 = dparser.parse(fechaPick4, fuzzy=True)
			#print(datePick4.strftime("%d/%m/%Y"))
		except Exception as e:
			raise e
		
		# Verificar que sea el tiro siguiente de la noche de ese mismo dia
		sameday = datePick3 == datePick4 == lastDate
		#print(sameday)
		if not sameday:
			#print('Todavia no se ha actualizado')
			return

		pick3 = getXpath(treePick3, '//*[@id="gameContentLeft"]/div[2]/div[2]/p[1]/span[@class="balls"]/text()')
		#print(pick3)

		pick4 = getXpath(treePick4, '//*[@id="gameContentLeft"]/div[2]/div[2]/p[1]/span[@class="balls"]/text()')
		#print(pick4)

		# Agregar tiro
		pick3 = pick3.replace('-','')
		pick4 = pick4.replace('-','')
		pick4 = pick4[:2] +'-'+ pick4[2:4]
		newTiro = lastDate.strftime("%d/%m/%Y") + '/N-' + pick3 + '-' + pick4

	new_tiro(newTiro)
	#print("Tiro agregado: " + newTiro)

main()
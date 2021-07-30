from django.shortcuts import render,redirect
import folium
import geocoder
from .forms import SearchPlacesForm
from .models import *
from django.contrib import messages
import re
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
from django.conf import settings
import json
import time
import os


# Create your views here.

def get_html_content(location,state,country):
	options = Options()
	options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
	options.add_argument('--headless')
	#options.add_argument("--example-flag")
	options.add_argument('--disable-dev-shm-usage')
	options.add_argument('--no-sandbox')
	options.add_argument('--disable-gpu')
	
	#options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"')
	#options.add_argument("--incognito")
	#options.add_argument('--ignore-certificate-errors-spki-list')
	#options.add_argument('--ignore-ssl-errors')
	
	driver = webdriver.Chrome(executable_path=str(os.environ.get("CHROMEDRIVER_PATH")), chrome_options=options)
	#chrome_driver_path = 'C:/Users/user/Desktop/projects/MapInn/chromedriver'
	#driver = webdriver.Chrome(executable_path = chrome_driver_path,chrome_options=options)
	#driver.set_page_load_timeout(30)
	#driver.implicitly_wait(10)

	location = location.replace(' ','%20')
	state = state.replace(' ','%20')
	country = country.replace(' ','%20')
	url = f'https://hotel.yatra.com/hotel-search/dom/search?city.name={location}&state.name={state}&country.name={country}'
	driver.get(url)
	
	content = driver.page_source
	
	#driver.quit()
	print(content)
	return content

def scrapeWebsite(html_content,state,country):
	hotel_list=[]
	address_list =[]
	ammenities_list=[]
	price_list =[]
	rating_list=[]
	
	soup = BeautifulSoup(html_content,'html.parser')
	
	articles = soup.find_all('article',attrs={'class':'full ng-scope'})
	for article in articles:
		for side in article.find_all('div',attrs={'class':'result-details-left'}):
			
			hotel_name = side.find('a',attrs={'class':'under-link ng-binding'}).text
			hotel_list.append(hotel_name)

			hotel_address = side.find('span',attrs={'class':'va-sub ng-binding'}).text
			hotel_address = hotel_address.replace('\xa0',' ')
			hotel_address=hotel_address+","+state+","+country
			address_list.append(hotel_address)

			ammenity_list=[]
			hotel_ammenity_list = side.find('ul',attrs={'class':'hotel-amenities-height-auto'})
			ammenity_list.append(hotel_ammenity_list.text.strip().replace('\n',' '))
			ammenities_list.append(ammenity_list)

			rating = side.find('span',attrs={'class':'trip-color ng-binding'}).text.strip()		
			rating_list.append(rating)

			price = side.find('span',attrs={'class':'bold ng-binding'}).text.strip()
			#print(price_div)
			#rate = re.findall('^([0-9]{1,3})(,[0-9]{3})*$',price_div)
			
			price_list.append(price)


	#creating a dataframe
	column = {'Name':hotel_list,'Address' : address_list, 'Price' : price_list, 'Rating' :rating_list,'Ammenities':ammenities_list}
	properties = pd.DataFrame(column)    
	return properties

def store_in_model(data):
	data['Full_Address'] = data[['Name', 'Address']].agg(','.join, axis=1)
	data = data['Full_Address']
	for index in data:
		if not Hotel.objects.filter(location=index).exists():
			g = geocoder.mapbox(index, key=settings.TOKEN_KEY)
			g = g.latlng
			lat = g[0]
			lng = g[1]
			h = Hotel(location=index,latitude=lat,longitude=lng)
			h.save()
	return data

def place_markers(m,hotels,data):
	
	for i in range(len(data.index)):
		name = hotels[i]
		hotel_loc = Hotel.objects.get(location=name)
		
		text = f"""
        <h2 style ="color:#167D7F">{data.iloc[i]['Name']}</h2><br>
        <div style="text-align:center;font-size:23px;color:#2F5061">{data.iloc[i]['Address']}</div>
        <div style="text-align:center;font-size:15px;color:#0C1446">Rating : {data.iloc[i]['Rating']}</div>
        <div style="text-align:center;font-size:20px;color:#0C1446">Price{data.iloc[i]['Price']}</div>   
        
            """
		folium.Marker([hotel_loc.latitude,hotel_loc.longitude], popup=folium.Popup(text, max_width = 400),
		 tooltip="Click for more").add_to(m)


def home(request):
	if request.method == "POST":
		form = SearchPlacesForm(request.POST)
		if form.is_valid():
			location = request.POST.get('location')
			loc = geocoder.osm(location)
			lng = loc.lng
			lat = loc.lat
			state = loc.json['state']
			country = loc.json['country']

			if(lng==None or lat == None):
				messages.error(request,'Entered Location is not valid')
				return redirect('home')
			else:
				html_content = get_html_content(location,state,country)
				data = scrapeWebsite(html_content,state,country)
				hotels = store_in_model(data[['Name','Address']])
				m = folium.Map(location = [lat,lng],zoom_start=12,)
				place_markers(m,hotels,data)
				m = m._repr_html_()

	else:
		m = folium.Map(location = [22,78],zoom_start=4,)
		form = SearchPlacesForm()
		m = m._repr_html_()

	context={'map':m,'form':form}
	return render(request,'maps/home.html',context)
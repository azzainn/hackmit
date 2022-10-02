"""
Project by: Sahal Ahmed, Ahmed Zain, Sebastian Losada
sources: 

https://impact.economist.com/sustainability/project/food-security-index/
https://www.geonames.org/
"""
import requests
import os
import csv
import pandas as pd
from bs4 import BeautifulSoup
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
import matplotlib.pyplot as plt

columns = ["Country", "Insecurity"]
with open("foodinsecurity.csv", mode="r", newline="") as file:
  filereader = csv.reader(file, delimiter=",", quotechar="|")
  df = pd.DataFrame(filereader, columns=columns)
  df = df.sort_values("Insecurity", ascending = True)
  top_25 = df.head(25)
  top_25.reset_index(inplace=True)

country_abbreviations = {"Syria": "SY", "Haiti":"HT","Yemen":"YE","Sierra Leone":"SL","Burundi":"BI","Madagascar":"MG","Nigeria":"NG","Venezuela":"VE","Sudan":"SD","Congo (Dem. Rep.)":"CD","Chad":"TD","Zambia":"ZM","Angola":"AO","Ethiopia":"ET","Guinea":"GN","Togo":"TG","Niger":"NE","Cameroon":"CM","Côte d'Ivoire":"CI","Mozambique":"MZ","Uganda":"UG","Malawi":"MW","Benin":"BJ","Tanzania":"TZ","Burkina Faso":"BF"}
countries = list(country_abbreviations.items())
url = "https://www.geonames.org/{}/largest-cities-in-{}.html"


def coords_to_tuple(coords):
  """
  splits coords {{string}} together into tuple
  removes '/', typecasts to floats
  '36.201/37.161' ---> (36.201,37.161)
  """
  
  latitude = []
  longitude = []
  add_to_lat = True
  
  for char in coords:
    if char != '/' and add_to_lat:
      latitude += char
    elif char == "/":
      add_to_lat = False
    else:
      longitude += char

  latitude_string = float("".join(latitude))
  longitude_string = float("".join(longitude))
  
  return (latitude_string, longitude_string)  


def get_pop_coords(dataframe):
  """
  Takes in a pandas dataframe, returns a list of dictionaries of populations and coordinates
  """
  pop_and_coords = []
  
  for index, row in dataframe.iterrows():
    
    pop_url = url.format(countries[index][1], countries[index][0]) 
    req_pop_url = requests.get(url=pop_url)
    soup = BeautifulSoup(req_pop_url.text, "html.parser")
    
    populations = []
    all_pop_tags = soup.find_all(class_="rightalign")
    
    for pop_tag in all_pop_tags:
      pop_text = pop_tag.get_text()
      populations.append(pop_text)

    coordinates = []
    all_hyperlink_tags = soup.find_all("a")
    for x, hyperlink_tag in enumerate(all_hyperlink_tags):
      hyperlink_tag_text = hyperlink_tag.get_text()
      found_num = False
      lat_long = []
      
      for char in hyperlink_tag_text:
        if char in "1234567890":
          found_num = True
        if found_num:
          lat_long += char
          if char == "\n":
            break
            
      lat_long_text = "".join(lat_long).replace(" ", "")
      if len(lat_long) != 0 and lat_long_text != "73":
        coordinates.append(lat_long_text)
        
    pop_and_coords.append({})
    for i in range(len(populations)):
      pop_and_coords[index][i] = coords_to_tuple(coordinates[i])
  return pop_and_coords


def optimal_location(pop_latlong_dict):
  """
  Parameters would be dict with pop_tag being the key,
  latitude/longitude in a tuple as the value

  {pop:(lat,long),pop:(lat,long), etc...}

  returns optimal latitude/longitude as tuple
  (opt_latitude, opt_longitude)
  [{1602264:(36.201, 37.161), 1569394:(33.51, 36.291), 775404:(34.727, 36.723), ...}, {next country}, {3rd country}]
  """
  opt_latitude = 0
  opt_longitude = 0
  pop_tag = 0

  for key, val in pop_latlong_dict.items():
    opt_latitude += val[0] * key
    opt_longitude += val[1] * key
    
    pop_tag += key
  
  opt_latitude /= pop_tag
  opt_longitude /= pop_tag
  
  opt_coord = (round(float(opt_latitude), 4), round(float(opt_longitude), 4))
  return opt_coord
  

def all_optimal_locations(listdict):
  """
  Takes in list of dictionaries,
  returns list of optimal locations
  """
  opt_locations = []

  for dict in listdict:
    opt_locations.append(optimal_location(dict))
  
  return opt_locations

pop_coords = get_pop_coords(top_25)
rows = []
columns = ["Country", "Latitude", "Longitude"]

for i, tuple in enumerate(all_optimal_locations(pop_coords)):
  rows.append({columns[0]: countries[i][0], columns[1]: tuple[0], columns[2]: tuple[1]})

with open("optimal_locations.csv", "w+") as csvfile:
  writer = csv.DictWriter(csvfile, fieldnames = columns)
  writer.writeheader()
  writer.writerows(rows)

# plotting
df = pd.read_csv("optimal_locations.csv", delimiter=",", skiprows=0, low_memory=False)
geometry = [Point(xy) for xy in zip(df["Longitude"], df["Latitude"])]
gdf = GeoDataFrame(df, geometry=geometry)

world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
gdf.plot(ax=world.plot(figsize=(10, 6)), marker="o", color="red", markersize=5)
plt.savefig("locations.jpg")
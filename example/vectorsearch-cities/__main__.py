from cmd import Cmd
import objectbox
import time
from .model import *
import csv
import os

def list_cities(cities):
    print("{:3s}  {:25s}  {:>9s}  {:>9s}".format("ID", "Name", "Latitude", "Longitude"))
    for city in cities:
        print("{:3d}  {:25s}  {:>9.2f}  {:>9.2f}".format(
        city.id, city.name, city.location[0], city.location[1]))

def list_cities_with_scores(city_score_tuples):
    print("{:3s}  {:25s}  {:>9s}  {:>9s}  {:>5s}".format("ID", "Name", "Latitude", "Longitude", "Score"))
    for (city,score) in city_score_tuples:
        print("{:3d}  {:25s}  {:>9.2f}  {:>9.2f}  {:>5.2f}".format(
        city.id, city.name, city.location[0], city.location[1], score))

class VectorSearchCitiesCmd(Cmd):
    prompt = "> "
    def __init__(self, *args):
        Cmd.__init__(self, *args)
        dbdir = "cities-db"
        new_db = not os.path.exists(dbdir)
        self._ob = objectbox.Builder().model(get_objectbox_model()).directory(dbdir).build()
        self._box = objectbox.Box(self._ob, City)
        self._name_prop: Property = City.get_property("name")
        self._location_prop: Property = City.get_property("location")
        if new_db: 
            with open(os.path.join(os.path.dirname(__file__), 'cities.csv')) as f:
                r = csv.reader(f) 
                cities = []
                for row in r:
                    city = City()
                    city.name = row[0]
                    city.location = [ row[1], row[2] ]
                    cities.append(city)
                self._box.put(*cities)

    def do_ls(self, name: str = ""):
        """list all cities or starting with <prefix>\nusage: ls [<prefix>]"""
        qb = self._box.query()
        qb.starts_with_string(self._name_prop, name)
        query = qb.build()
        list_cities(query.find())

    def do_city_neighbors(self, args: str):
        """find <num> (default: 5) next neighbors to city <name>\nusage: city_neighbors <name> [,<num>]"""
        try:
            args = args.split(',')
            if len(args) > 2:
                raise ValueError()
            city = args[0]
            if len(city) == 0:
                raise ValueError()
            num = 5
            if len(args) == 2:
                num = int(args[1])
            qb = self._box.query()
            qb.equals_string(self._name_prop, city)
            query = qb.build()
            cities = query.find()
            if len(cities) == 1:
                location = cities[0].location
                qb = self._box.query()
                qb.nearest_neighbors_f32(self._location_prop, location, num+1) # +1 for the city
                qb.not_equals_string(self._name_prop, city)
                neighbors = qb.build().find_with_scores()
                list_cities_with_scores(neighbors)
            else:
                print(f"no city found named '{city}'")
        except ValueError: 
            print("usage: city_neighbors <name>[,<num: default 5>]")
    
    def do_neighbors(self, args):
        """find <num> neighbors next to geo-coord <lat> <long>.\nusage: neighbors <num>,<latitude>,<longitude>"""
        try:
            args = args.split(',')
            if len(args) != 3:
                raise ValueError()
            num = int(args[0])
            geocoord = [ float(args[1]), float(args[2]) ]
            qb = self._box.query()
            qb.nearest_neighbors_f32(self._location_prop, geocoord, num)
            neighbors = qb.build().find_with_scores()
            list_cities_with_scores(neighbors)
        except ValueError: 
            print("usage: neighbors <num>,<latitude>,<longitude>")
    
    def do_add(self, args: str):
        """add new location\nusage: add <name>,<lat>,<long>"""
        try:
            args = args.split(',')
            if len(args) != 3:
                raise ValueError()
            name = str(args[0])
            lat = float(args[1])
            long = float(args[2])
            city = City()
            city.name = name
            city.location = [lat,long] 
            self._box.put(city)
        except ValueError: 
            print("usage: add <name>,<latitude>,<longitude>")
   
    def do_exit(self, _):
        """close the program"""
        raise SystemExit()


if __name__ == '__main__':
    app = VectorSearchCitiesCmd()
    app.cmdloop('Welcome to the ObjectBox vectorsearch-cities example. Type help or ? for a list of commands.')

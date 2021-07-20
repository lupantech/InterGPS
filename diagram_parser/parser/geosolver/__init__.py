from geosolver import settings
from geosolver.database.geoserver_interface import GeoserverInterface

__author__ = 'minjoon'

geoserver_interface = GeoserverInterface(settings.GEOSERVER_URL)

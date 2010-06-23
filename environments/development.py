#  This file is part of TxtAlert.
#
#  TxtALert is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  TxtAlert is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with TxtAlert.  If not, see <http://www.gnu.org/licenses/>.

from defaults import *
import os

DEBUG = True

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = 'txtalert_dev'
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_PORT = ''

OPERA_SERVICE = os.environ['OPERA_SERVICE']
OPERA_PASSWORD = os.environ['OPERA_PASSWORD'] 
OPERA_CHANNEL = os.environ['OPERA_CHANNEL']

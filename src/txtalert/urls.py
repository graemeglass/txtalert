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


from os import path
from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django.conf import settings

admin.autodiscover()

# web site
urlpatterns = patterns('',
    # Uncomment this for admin docs:
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'', include('txtalert.apps.general.jquery.urls')),
    (r'^therapyedge/', include('txtalert.apps.therapyedge.urls')),
    (r'^bookingtool/', include('txtalert.apps.bookingtool.urls')),
    (r'^geckoboard/', include('txtalert.apps.geckoboard.urls')),
    # (r'^sms/', include('opera.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^static/(.*)$', 'django.views.static.serve', \
                            {'document_root': settings.MEDIA_ROOT}, "static"),
)

# web API
urlpatterns += patterns('',
   (r'^api/v1/', include('txtalert.apps.api.urls')),
)
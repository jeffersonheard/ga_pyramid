from django.conf.urls.defaults import patterns, url
from ga_ows.views.wms import WMS
from views import WMSAdapter
from models import Pyramid

#
# This file maps views to actual URL endpoints. 
#

urlpatterns = patterns('',
    # The following URL will expose a sample "Alert" model as a WMS service given the stylesheets in ss.py.  
    url(r'^wms', WMS.as_view(adapter=WMSAdapter(cls=Pyramid, application='ga_pyramid', styles={}))),
)

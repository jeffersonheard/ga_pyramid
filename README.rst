ga_pyramid - Geoanalytics Image Pyramid
#######################################

The Image Pyramid is a data model within Geoanalytics to hold tiled pyramidal
datasets.  Like the DataCube on which it is based, Pyramids can contain images
at multiple times and elevations, and WMS queries support these. 

The Image Pyramid is distributed as a reusable Django app.  Installation is as 
simple as running::

   $ pip install mongoengine pymongo gdal # install dependencies
   $ git clone git://github.com/JeffHeard/ga_ows.git
   $ cd ga_ows
   $ python setup.py install
   $ cd ..
   $ cd ga_pyramid
   $ python setup.py install

And then adding ``ga_ows`` and ``ga_pyramid`` to your list of INSTALLED_APPS in
settings.py.  You will also need to add ``ga_pyramid.urls`` to your base
urls.py file.

External Dependencies
=====================

ga_pyramid requires MongoDB to work properly.  MongoDB and MongoEngine should
be setup via the Django settings.  If you are unfamiliar with how to do this,
consult `mongoengine.org`_ . 

.. _mongoengine.org: http://mongoengine.org

Loading a Pyramid
#################

Loading a pyramid is a simple manage.py command.  To load a pyramid, navigate
to a directory containing a collection of georeferenced images and type::

   $ python $VIRTUAL_ENV/ga/manage.py load_pyramid [options] mypyramid_name *.tif

Where options are any of::

  -v VERBOSITY, --verbosity=VERBOSITY
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=all output
  --settings=SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath=PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Print traceback on exception
  --drop                drop the old pyramid before loading a new one.
  --levels=LEVELS       the number of levels of pyramid to calculate - the
                        default is 7
  --srs=SRS             the spatial reference system that the tiles are in
                        (default is EPSG:900913, the Google Mercator
                        projection
  --compress=COMPRESS   JPEG | LZW | PACKBITS | DEFLATE | CCITTRLE | CCITTFAX3
                        | CCITTFAX4 | NONE
  --format=FORMAT       GTiff | PNG | JPEG
  --quality=QUALITY     JPEG encoding quality
  --interp=INTERPOLATION
                        Interpolation : bilinear | near | cubic | cubicspline
                        | lanczos
  --photometric=PHOTOMETRIC
                        Set to YCBCR if using JPEG TIFF compression : MINISBLA
                        CK/MINISWHITE/RGB/CMYK/YCBCR/CIELAB/ICCLAB/ITULAB
  --data_type=DATA_TYPE
                        {Byte/Int16/UInt16/UInt32/Int32/Float32/Float64/CInt16
                        /CInt32/CFloat32/CFloat64}
  --create_options=CREATE_OPTIONS
                        driver specific creation options for GDAL
  --size=SIZE           number of pixels per row/column
  --time=TIME           [YYYY-MM-DD-hh:mm:ss] The UTC time value for this
                        pyramid, if there is one
  --elevation=ELEVATION
                        The elevation value for this pyramid if there is one
  --append              Append to the current pyramid (useful for adding times
                        or elevations
  --version             show program's version number and exit
  -h, --help            show this help message and exit

Be sure when loading a pyramid that MongoDB is up and running.  GDAL formats
for GeoTiff, PNG, and JPEG are supported.  GeoTIFF is the default format. If
you use JPEG or PNG, you will have to pass your own creation options via
--create_options.  These options will be passed to GDAL via gdal_retile.py.
The future path for this software is to make the use of gdal_retile.py
optional, as it does no parallel processing at all, and we want to support
parallel retiling. 

Note --srs does NOT transform tiles.  It is simply there as an option if your
tileset doesn't have a PRJ file and is not a collection of GeoTIFFs.  

Size is by default 1024.  This generally need not be changed.

Accessing loaded pyramids via WMS
=================================

Once you have a loaded pyramid, you can access it via WMS with the ``layers``
parameter being set to the layer name::

   http://localhost:8000/ga_pyramid/wms?service=WMS&request=GetMap&version=1.1.0&layers=mypyramid_name&bbox={x0},{y0},{x1},{y1}&format=png&srs=EPSG:900913



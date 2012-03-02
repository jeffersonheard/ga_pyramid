"""The pyramid data model is designed mainly for exposing via WMS.  Its best
use-case is very large raster datasets. The Pyramid contains tiles at different
zoom levels to make retrieval and stitching blazingly fast no matter how much
of the dataset you are trying to look at at once.  To use the Pyramid, you will
want to use :file:`pyramid_loader.py`, which is similar to
:file:`gdal_retile.py` in the GDAL package, but contains a few extra options.
See ``pyramid_loader.py --help`` for more details.

"""

from mongoengine import *

class Pyramid(Document):
    """
    Class that encapuslates Pyramid metadata.  The metadata fields are:
    
    .. :py:attribute: name 
        The name of the pyramid (indexed)
        * :py:attribute:`tile_width` - The width of the tile in pixels.
        * :py:attribute:`tile_height` - THe height of contained tiles in pixels.
        * :py:attribute:`srs` - The spatial reference identifier (EPSG code or PostGIS ID)
        * :py:attribute:`levels` - The number of zoom levels contained
        * :py:attribute:`create_options` - The options used on the command line to create the pyramid
        * :py:attribute:`indices` - The spatial index files for each level of pyramid.
        * :py:attribute:`data_type` - The data type of pixels in the pyramid.
        * :py:attribute:`raster_count` - The total number of tiles in the pyramid.

    One method is important.  If you want to drop a pyramid, you must use::

        pyramid.drop()

    This drops all tile objects associated with the pyramid as well as the
    pyramid itself.
    """
    name = StringField(unique=True)
    tile_width = IntField()
    tile_height = IntField()
    srs = StringField()
    levels = IntField()
    create_options = DictField()
    pxsize_at_levels = ListField(FloatField())
    indices = ListField(StringField())
    data_type = IntField()
    raster_count = IntField()

    meta = {
        'indexes' : ['name']
    }

    def drop(self):
        Tile.objects(pyramid=self).delete()
        self.delete(safe=True)

    @property
    def tiles(self):
        return Tile.objects.filter(pyramid=self)

class Tile(Document):
    """
    Class that encapsulates tiles.  The most important field is "data".  This
    contains a GDAL dataset in GeoTIFF form that is the tile data itself.  If
    you need to load this data manually for some reason, see the
    :py:class:`ga.ows.pyramid.PyramidWMSAdapter` for an example of how to do
    this.  

    Attributes:

        * :py:attribute:`pyramid` - The pyramid this tile is a part of.
        * :py:attribute:`tile_name` - The filename this tile had.
        * :py:attribute:`level` - The zoom level this tile is a part of
        * :py:attribute:`data` -  The data itself.
        * :py:attribute:`time` -  The time that goes with this tile.
        * :py:attribute:`elevation` - The elevation that goes with this tile.

    Note, deleting individual tiles is a bad idea.  They are in the indices and
    cannot be removed from there easily.  Don't do it.  Drop the whole pyramid
    and load it again, but there should be no reason to delete tiles.

    For quick querying of tiles outside the WMS interface, the following indices are defined:

        * pyramid
        * pyramid + level
        * pyramid + level + tile_name
        * pyramid + level + time
        * pyramid + level + time + elevation

    """
    pyramid = ReferenceField(Pyramid)
    tile_name = StringField()
    level = IntField()
    data = BinaryField()
    time = DateTimeField()
    elevation = FloatField()

    meta = {
        'indexes' : [
            'pyramid', 
            ('pyramid', 'level'), 
            ('pyramid', 'level', 'tile_name'), 
            ('pyramid', 'level', 'time'), 
            ('pyramid', 'level', 'time', 'elevation')
        ]
    }


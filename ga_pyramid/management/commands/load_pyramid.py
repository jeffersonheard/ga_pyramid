from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
import subprocess
import os
import sys
import tempfile
from django.conf import settings
import shutil
from ga_pyramid.models import *
from osgeo import gdal, ogr


class Command(BaseCommand):
    DataTypes = {
        "Byte" : gdal.GDT_Byte,
        "Int16" : gdal.GDT_Int16,
        "UInt16" : gdal.GDT_UInt16,
        "UInt32" : gdal.GDT_UInt32,
        "Int32" : gdal.GDT_Int32,
        "Float32" : gdal.GDT_Float32,
        "Float64" : gdal.GDT_Float64,
        "CInt16" : gdal.GDT_CInt16,
        "CInt32" : gdal.GDT_CInt32,
        "CFloat32" : gdal.GDT_CFloat32,
        "CFloat64" : gdal.GDT_CFloat64
    }

    args = '<name directrory_or_glob ...>'
    help = 'Loads a pyramid into the database'
    option_list = BaseCommand.option_list + (
        make_option('--drop', action='store_true', dest='drop', default=False, help='drop the old pyramid before loading a new one.'),
        make_option('--levels', action='store', dest='levels', default='7', help='the number of levels of pyramid to calculate - the default is 7'),
        make_option('--srs', action='store', dest='srs', default='EPSG:900913', help='the spatial reference system that the tiles are in (default is EPSG:900913, the Google Mercator projection' ),
        make_option('--compress', action='store', dest='compress', default='JPEG', help='JPEG | LZW | PACKBITS | DEFLATE | CCITTRLE | CCITTFAX3 | CCITTFAX4 | NONE'),
        make_option('--format', action='store', dest='format', default='GTiff', help='GTiff | PNG | JPEG'),
        make_option('--quality', action='store', dest='quality', default='75', help='JPEG encoding quality'),
        make_option('--interp', action='store', dest='interpolation', default='bilinear', help='Interpolation : bilinear | near | cubic | cubicspline | lanczos'),
        make_option('--photometric', action='store', dest='photometric', default=None, help='Set to YCBCR if using JPEG TIFF compression : MINISBLACK/MINISWHITE/RGB/CMYK/YCBCR/CIELAB/ICCLAB/ITULAB'),
        make_option('--data_type', action='store', dest='data_type', default='Byte', help='{Byte/Int16/UInt16/UInt32/Int32/Float32/Float64/CInt16/CInt32/CFloat32/CFloat64}'),
        make_option('--create_options', action='store', dest='create_options', default=None, help='driver specific creation options for GDAL'),
        make_option('--size', action='store', dest='size', default='1024', help='number of pixels per row/column'),
        make_option('--time', action='store', dest='time', default=None, help='[YYYY-MM-DD-hh:mm:ss] The UTC time value for this pyramid, if there is one'),
        make_option('--elevation', action='store', dest='elevation', default=None, help='The elevation value for this pyramid if there is one'),
        make_option('--append', action='store_true', dest='append', default=False, help='Append to the current pyramid (useful for adding times or elevations')
    )

    def handle(self, *args, **options):
        options['name'] = args[0]
        options['args'] = args[1:]

        if options['time']:
            options['time'] = datetime.strptime('%Y-%m-%d-%H:%M:%S')
        if options['elevation']:
            options['elevation'] = float(options['elevation'])

        levels = int(options['levels'])
        name = options['name']

        if options['drop']:
            pyr = Pyramid.objects(name=name).first()
            if pyr:
                pyr.drop()

        coptions = []
        if options['format'] == 'GTiff':
            if options['compress'] == 'JPEG' and not options['photometric']:
                options['photometric'] = 'YCBCR'
            elif not options['photometric']:
                options['photometric'] = 'RGB'

            coptions.append('-co COMPRESS={compress}'.format(**options))
            if options['compress'] == 'JPEG':
                coptions.append('-co JPEG_QUALITY={quality}'.format(**options))
            if options['photometric']:
                coptions.append('-co PHOTOMETRIC={photometric}'.format(**options))
            if options['create_options']:
                coptions.extend(map(lambda x: '-co '+x, create_options.split(',')))
        else:
            coptions.extend(map(lambda x: '-co '+x, create_options.split(',')))

        path = tempfile.mkdtemp(prefix='load_pyramid-')

        coptions = ' '.join(coptions)
        options['args'] = ' '.join(options['args'])
        options['coptions'] = coptions
        options['path'] = path

        if hasattr(settings, 'GDAL_BIN'):
            options['gdal_command'] = os.path.join(settings.GDAL_BIN, 'gdal_retile.py')
        else:
            options['gdal_command'] = 'gdal_retile.py'

        # use gdal_retile for now to load the tiles.  We will eliminate this in the future.
        subprocess.Popen(
            '{gdal_command} -v -useDirForEachRow -targetDir {path} -ps {size} {size} -tileIndex {name} -levels {levels} -r {interpolation} -of {format} -ot {data_type} {coptions} {args}'.format(**options),
            shell=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            bufsize=-1,
        ).wait()

        #
        # create a pyramid object
        #
        index_dir = os.path.join(settings.MEDIA_ROOT, 'ga_pyramid', 'indices', name)

        pyramid = Pyramid.objects(name=name).first()
        if pyramid and not options['append']:
            raise InvalidCollectionError('Pyramid already exists.  Either add --drop or --append to your command line')
        elif not pyramid:
            pyramid = Pyramid(
                name = name,
                tile_width = int(options['size']),
                tile_height = int(options['size']),
                srs=open(os.path.join(path, '0', name+'.prj')).read(),
                levels=levels,
                create_options = options,
                pxsize_at_levels = [],
                indices = [os.path.join(index_dir, '{name}_{level}.shp'.format(name=name, level=level)) for level in range(levels+1)],
                data_type = Command.DataTypes[options['data_type']],
                raster_count = 0,
            )
            pyramid.save()

        # copy indices to STATIC_ROOT/pyramids/indices

        try:
            os.makedirs(index_dir)
        except OSError: # file exists, that's okay
            pass

        try:
            for level in range(levels+1):
                print("loading level {level}".format(level=level))
                index_name = os.path.join(index_dir, '{name}_{level}'.format(name=name, level=level))

                try:
                    os.makedirs(os.path.join(index_dir, str(level)))
                except OSError:
                    pass

                shutil.copyfile(os.path.join(path, str(level), name+'.shp'), index_name + '.shp')
                shutil.copyfile(os.path.join(path, str(level), name+'.shx'), index_name + '.shx')
                shutil.copyfile(os.path.join(path, str(level), name+'.dbf'), index_name + '.dbf')
                shutil.copyfile(os.path.join(path, str(level), name+'.prj'), index_name + '.prj')

                # open indices and add each tile in the index as a Tile object in the Pyramid.
                ds = ogr.Open(index_name + '.shp')
                index = ds.GetLayer(0)

                tile_ds = gdal.Open(os.path.join(path, str(level), index.next().location))
                xs, xw, _0, ys, _1, yw = tile_ds.GetGeoTransform()
                pyramid.pxsize_at_levels.append(xw)
                pyramid.raster_count = tile_ds.RasterCount

                index.ResetReading()
                for tile in index:
                    sys.stderr.write('.')
                    sys.stderr.flush()
                    Tile.objects.create(
                        pyramid=pyramid,
                        tile_name = tile.location,
                        level = level,
                        data = open(os.path.join(path, str(level), tile.location)).read(),
                        time = options['time'],
                        elevation = options['elevation']
                    )

            pyramid.save()
            print("Loaded pyramid. {count} tiles loaded with a total of {levels} levels.".format(count=pyramid.tiles.count(), levels=levels))
        finally:
            shutil.rmtree(options['path'])




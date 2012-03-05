from ga_ows.views.wms import WMSAdapterBase
from django.http import HttpResponse
from osgeo import ogr, gdal, osr
from ga_pyramid.models import Pyramid, Tile
import logging
import json

log = logging.getLogger(__name__)

class WMSAdapter(WMSAdapterBase):
    def get_feature_info(self, wherex, wherey, srs, query_layers, 
                         info_format, feature_count, exceptions, *args, **kwargs):
        pixel = self.get_2d_dataset(
            bbox=(wherex, wherey, wherex, wherey), 
            width=1, height=1, query_layers=query_layers)
       
        arr = None
        if pixel:
            arr = pixel.ReadAsArray()

        return HttpResponse(json.dumps(arr), mimetype='text/plain')

    def get_2d_dataset(self, bbox, width, height, query_layers, styles=None, **args):
        pyramid = Pyramid.objects(name=query_layers[0]).first()

        # see if we need to transform the dataset
        s_srs = osr.SpatialReference()
        t_srs = osr.SpatialReference()
        default_srid=Pyramid.objects(name=query_layers[0]).first().srs
        s_srs.ImportFromWkt(default_srid.decode('ascii'))

        if 'proj' in args:
            t_srs.ImportFromProj4(args['proj'])
        elif 'srs' in args and args['srs']:
            srid = args['srs']

            if srid.startswith('EPSG'):
                srid = int(srid[5:])
                t_srs.ImportFromEPSG(srid)
            else:
                try:
                    srid = int(srid)
                    t_srs.ImportFromEPSG(srid)
                except:
                    t_srs.ImportFromWkt(srid)
        else:
            t_srs = s_srs

        crx = osr.CoordinateTransformation(t_srs, s_srs)

        # figure out the pixel size.  if we're only after one pixel, like for GetFeatureInfo,
        # it's likely that pxsize will be 0.  In that case, set the pixel size to be the 
        # smallest available.
        minx,miny,maxx,maxy = bbox
        tminx, tminy, tmaxx, tmaxy = bbox

        if s_srs != t_srs:
            minx, miny, _0 = crx.TransformPoint(minx, miny, 0)
            maxx, maxy, _0 = crx.TransformPoint(maxx, maxy, 0)

        pxsize = (maxx-minx) / width
        print pxsize
        print pyramid

        # case of only looking for one pixel
        if pxsize == 0:
            pxsize = pyramid.pxsize_at_levels[-1]
            maxx = maxx+pxsize
            maxy = maxy+pxsize

        # start with the furthest zoomed out tiles and work our way in, searching for the 
        # nearest level to the query
        l = 0
        p = 999999999
        for level, px in enumerate(pyramid.pxsize_at_levels):
            if abs(px-pxsize) < p:
                l = level
                p = abs(px-pxsize)

        
        # open the index for that level, filter it by our bounding box.
        dataset = ogr.Open(pyramid.indices[l].encode('ascii'))
        index = dataset.GetLayer(0)
        index.ResetReading()
        index.SetSpatialFilterRect(minx, miny, maxx, maxy)
        f = index.GetNextFeature()

        # retrieve tiles
        tiles = []
        while f:
            Tile.objects.ensure_index('tile_name')
            Tile.objects.ensure_index('pyramid', 'tile_name')
            t = Tile.objects(pyramid=pyramid, level=l, tile_name=f.location).first()
            fl = gdal.FileFromMemBuffer('/vsimem/' + t.tile_name, t.data)
            tiles.append(gdal.Open('/vsimem/' + t.tile_name))
            f = index.GetNextFeature()
            print t
        del index # close the index

        # create our output dataset and stitch tiles into it by projecting them in.
        output = gdal.GetDriverByName('MEM').Create( "TEMP", width, height, pyramid.raster_count, pyramid.data_type, [])
        output.SetGeoTransform([tminx,(tmaxx-tminx)/width,0,tmaxy,0,(tminy-tmaxy)/height])
        output.SetProjection(t_srs.ExportToWkt())
        for tile in tiles:
            print tile.GetGeoTransform()
            print output.GetGeoTransform()
            gdal.ReprojectImage(tile, output, None, None, gdal.GRA_Bilinear)

        return output

    def layerlist(self):
        for p in Pyramid.objects():
            yield p.name

    def nativesrs(self, layer):
        return Pyramid.objects(name=layer).first().srs

    def nativebbox(self, layer):
        p = Pyramid.objects(name=layer).first()
        o = ogr.Open(p.indices[-1].encode('ascii'))
        l = o.GetLayer(0)
        minx,maxx,miny,maxy = l.GetExtent()
        del o
        return minx,miny,maxx,maxy

    def styles(self):
        return self.styles.keys()


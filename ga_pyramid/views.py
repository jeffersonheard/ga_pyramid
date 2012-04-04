from collections import defaultdict
from ga_ows.views.wms import WMSAdapterBase, WMSCache
from django.http import HttpResponse
from osgeo import ogr, gdal, osr
from django.contrib.gis import gdal as djgdal
from django.contrib.gis.geos import Point
from ga_pyramid.models import Pyramid, Tile
import logging
import json

log = logging.getLogger(__name__)

class WMSAdapter(WMSAdapterBase):
    def __init__(self, styles=None, requires_time=False, requires_elevation=False, requires_version=False):
        super(WMSAdapter, self).__init__(styles=styles, requires_time=requires_time, requires_elevation=requires_elevation, requires_version=requires_version)
        self.cache = WMSCache(collection='pyramid__wms_cache')

    def get_feature_info(self, wherex, wherey, srs, query_layers, 
                         info_format, feature_count, exceptions, *args, **kwargs):
        pixel = self.get_2d_dataset(query_layers,srs, (wherex, wherey, wherex, wherey), 1, 1, **kwargs)
        arr = None
        if pixel:
            arr = pixel.ReadAsArray()

        return HttpResponse(json.dumps(arr), mimetype='text/plain')

    def get_2d_dataset(self, layers, srs, bbox, width, height, styles=None, bgcolor=None, transparent=False, time=None, elevation=None, v=None, filter=None, **kwargs):
        pyramid = Pyramid.objects(name=layers[0]).first()
        minx, miny, maxx, maxy = bbox

        # see if we need to transform the dataset
        default_srid=Pyramid.objects(name=layers[0]).first().srs

        s_srs = djgdal.SpatialReference(default_srid.decode('ascii'))

        print srs
        if not srs:
            t_srs = djgdal.SpatialReference(default_srid.decode('ascii'))
        else:
            t_srs = djgdal.SpatialReference(srs)

        #print t_srs, s_srs

        s_mins = Point(minx, miny, srid=t_srs.wkt)
        s_maxs = Point(maxx, maxy, srid=t_srs.wkt)
        s_mins.transform(s_srs.srid)
        s_maxs.transform(s_srs.srid)

        # figure out the pixel size.  if we're only after one pixel, like for GetFeatureInfo,
        # it's likely that pxsize will be 0.  In that case, set the pixel size to be the 
        # smallest available.
        tminx, tminy, tmaxx, tmaxy = bbox
        minx = s_mins.x
        maxx = s_maxs.x
        miny = s_mins.y
        maxy = s_maxs.y
        pxsize = (maxx-minx) / width

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

        del index # close the index

        # create our output dataset and stitch tiles into it by projecting them in.
        output = gdal.GetDriverByName('MEM').Create( "TEMP", width, height, pyramid.raster_count, pyramid.data_type, [])
        output.SetGeoTransform([tminx,(tmaxx-tminx)/width,0,tmaxy,0,(tminy-tmaxy)/height])
        output.SetProjection(t_srs.wkt)


        #print output.GetGeoTransform()

        for tile in tiles:
            #print tile.GetGeoTransform()
            #print tile.GetProjection()
            #print output.GetProjection()
            gdal.ReprojectImage(tile, output, None, None, gdal.GRA_Bilinear)

        return output

    def layerlist(self):
        for p in Pyramid.objects():
            yield p.name

    def nativesrs(self, layer):
        return Pyramid.objects(name=layer).first().srs

    def nativebbox(self):
        p = Pyramid.objects().first() # this is a bug.  nativebbox should take a layer, but currently doesn't.
        o = ogr.Open(p.indices[-1].encode('ascii'))
        l = o.GetLayer(0)
        minx,maxx,miny,maxy = l.GetExtent()
        del o
        return minx,miny,maxx,maxy

    def styles(self):
        if self.styles:
            return self.styles.keys()
        else:
            return {}

    def get_cache_record(self, layers, srs, bbox, width, height, styles, format, bgcolor, transparent, time, elevation, v, filter, **kwargs):
        locator = {
            'layers' : layers,
            'srs' : srs,
            'bbox' : bbox,
            'width' : width,
            'height' : height,
            'styles' : styles,
            'format' : format,
            'bgcolor' : bgcolor,
            'transparent' : transparent,
            'time' : time,
            'elevation' : elevation,
            'v' : v,
            'filter' : filter
        }

        return self.cache.locate(**locator)

    def get_service_boundaries(self):
        return self.nativebbox()

    def get_layer_descriptions(self):
        ret = []
        for pyramid in Pyramid.objects.all():
            layer = dict()
            layer['name'] = pyramid.name
            layer['title'] = pyramid.title
            layer['srs'] = pyramid.srs
            layer['queryable'] = True
            o = ogr.Open(pyramid.indices[-1].encode('ascii'))
            l = o.GetLayer(0)
            minx,maxx,miny,maxy = l.GetExtent()
            layer['minx'] = minx
            layer['miny'] = miny
            layer['maxx'] = maxx
            layer['maxy'] = maxy
            s_srs = osr.SpatialReference()
            s_srs.ImportFromWkt(pyramid.srs)
            t_srs = osr.SpatialReference()
            t_srs.ImportFromEPSG(4326)
            crx = osr.CoordinateTransformation(s_srs, t_srs)
            ll_minx, ll_miny, _0 = crx.TransformPoint(minx, miny, 0)
            ll_maxx, ll_maxy, _0 = crx.TransformPoint(maxx, maxy, 0)

            layer['ll_minx'] = ll_minx
            layer['ll_miny'] = ll_miny
            layer['ll_maxx'] = ll_maxx
            layer['ll_maxy'] = ll_maxy
            layer['styles'] = []
            if isinstance(self.styles, dict):
                for style in self.styles.keys():
                    layer['styles'].append({
                        "name" : style,
                        "title" : style,
                        "legend_width" : 0,
                        "legend_height" : 0,
                        "legend_url" : ""
                    })
                    if hasattr(self.styles[style], 'legend_url'):
                        layer['styles'][-1]['legend_url'] = self.styles[style].legend_url
            ret.append(layer)
        return ret

    def get_valid_elevations(self, **kwargs):
        if 'layers' not in kwargs:
            return []
        else:
            p = Pyramid.objects(name=layers[0]).first()
            qs = Tile.objects(pyramid=p)
            if 'filter' in kwargs:
                qs = qs.filter(**kwargs['filter'])
            return qs.distinct('elevation')

    def get_valid_times(self, **kwargs):
        if 'layers' not in kwargs:
            return []
        else:
            p = Pyramid.objects(name=layers[0]).first()
            qs = Tile.objects(pyramid=p)
            if 'filter' in kwargs:
                qs = qs.filter(**kwargs['filter'])
            return qs.distinct('time')

    def get_valid_versions(self, group_by=None, **kwargs):
        if 'layers' not in kwargs:
            return []
        else:
            p = Pyramid.objects(name=layers[0]).first()
            qs = Tile.objects(pyramid=p)
            if 'filter' in kwargs:
                qs = qs.filter(**kwargs['filter'])
            return qs.distinct('version')

    def cache_result(self, item, **kwargs):
        locator = kwargs
        if 'fresh' in locator:
            del locator['fresh']
        self.cache.save(item, **kwargs)

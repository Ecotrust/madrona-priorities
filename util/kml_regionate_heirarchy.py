from collections import namedtuple
from django.contrib.gis.gdal import DataSource
import os
import sys
import zipfile

#URL = "http://usfw.labs.ecotrust.org/kmltest/"
URL = "./"
kmz = False
if kmz:
    extension = "kmz"
else:
    extension = "kml"
test = True 

Level = namedtuple('Level',['ds', 'simplify', 'uidfield','parent_uidfield'])

if test:
    INDIR = "/home/mperry/subset/input1/"
    OUTDIR = "/home/mperry/subset/output1"
    URL = "http://a.perrygeo.net/output1/"
    LEVELS = [
        Level(DataSource(INDIR + 'huc6.shp'), 0.003, 'HUC_6', None),
        Level(DataSource(INDIR + 'huc8.shp'), 0.001, 'HUC_8', 'HUC_6'),
        Level(DataSource(INDIR + 'huc10.shp'), 0.0001, 'HUC_10', 'HUC8'),
        Level(DataSource(INDIR + 'huc12.shp'), 0.00001, 'HUC_12', 'HUC_10'),
    ]
else:
    INDIR = "/home/mperry/subset/input2/"
    OUTDIR = "/home/mperry/subset/output2"
    LEVELS = [
        Level(DataSource(INDIR + 'huc6.shp'), 0.003, 'HUC_6', None),
        Level(DataSource(INDIR + 'HUC8_PNW_prj.shp'), 0.001, 'HUC_8', 'HUC_6'),
        Level(DataSource(INDIR + 'HUC10_PNW_prj.shp'), 0.0001, 'HUC_10', 'HUC8'),
        Level(DataSource(INDIR + 'HUC12.shp'), 0.00001, 'HUC_12', 'HUC_10'),
    ]

if not os.path.exists(OUTDIR):
    os.mkdir(OUTDIR)

kmls = {}

def lfind(needle, haystack):
    z=-1
    while 1:
        try:
            z = haystack.index(needle, z+1)
            yield z
        except:
            break

def name_callback(huc):
    return "HUC %s" % huc

def desc_callback(huc):
    level = len(huc)/2
    return "Level %s HUC" % level

def drilldown(levelnum, levels, parent=None):
    for levelnum in range(len(levels)):
        level = levels[levelnum]
        print level
        if levelnum < len(levels)-1: 
            if levelnum == 0:
                kmlfile = 'doc.%s' % (extension,)
                kmls[kmlfile] = (levelnum, [
                    {'geom': f.geom, 
                     'uid': f.get(level.uidfield),
                     'name': name_callback(f.get(level.uidfield)),
                     'desc': desc_callback(f.get(level.uidfield)) 
                    } for f in level.ds[0]])

            children_layer = levels[levelnum+1].ds[0]
            children_parent_uids = children_layer.get_fields(levels[levelnum+1].parent_uidfield)
            for feature in level.ds[0]:
                uid = feature.get(level.uidfield)
                kmlfile = "%s.%s" % (uid,extension)
                child_puidf = levels[levelnum+1].parent_uidfield
                child_uidf = levels[levelnum+1].uidfield
                indexes = list(lfind(uid,children_parent_uids))
                children = []
                for i in indexes:
                    f = children_layer[i]
                    children.append({
                        'geom': f.geom, 
                        'uid': f.get(child_uidf),
                        'name': name_callback(f.get(child_uidf)),
                        'desc': desc_callback(f.get(child_uidf)) 
                        })

                kmls[kmlfile] = (levelnum+1, children)
        else:
            return

def write_kmls(kmls):
    kmlhead = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2" 
         xmlns:atom="http://www.w3.org/2005/Atom" 
         xmlns:mm="http://marinemap.org" 
         xmlns:gx="http://www.google.com/kml/ext/2.2">
    <Document>
    <name>Watersheds</name>
    <open>1</open>
    <visibility>1</visibility>
    <Style id="default">
        <BalloonStyle>
            <bgColor>ffeeeeee</bgColor>
            <text> <![CDATA[
                <font color="#1A3752"><strong>$[name]</strong></font><br />
                <font color="#1A3752">$[description]</strong></font><br />

            ]]> </text>
        </BalloonStyle>
        <LabelStyle>
            <color>ffffffff</color>
            <scale>0.8</scale>
        </LabelStyle>
        <LineStyle>
            <color>9900ffff</color>
            <width>3.5</width>
        </LineStyle>
        <PolyStyle>
            <color>00ffffff</color>
        </PolyStyle>
    </Style>
    """

    kmlfoot = """
    </Document>
    </kml>
    """

    netlink = """
    <NetworkLink>
    <name>%s</name>
    <Region>
      <LatLonAltBox>
        <west>%s</west>
        <south>%s</south>
        <east>%s</east>
        <north>%s</north>
      </LatLonAltBox>
      <Lod>
        <minLodPixels>356</minLodPixels>
        <maxLodPixels>%s</maxLodPixels>
      </Lod>
    </Region>
    <Link>
      <href>%s</href>
      <viewRefreshMode>onRegion</viewRefreshMode>
    </Link>
    </NetworkLink>
    """

    region = """
    <Region>
      <!-- Region for top-level placemarks -->
      <LatLonAltBox>
        <west>%s</west>
        <south>%s</south>
        <east>%s</east>
        <north>%s</north>
      </LatLonAltBox>
      <Lod>
        <minLodPixels>-1</minLodPixels>
        <maxLodPixels>512</maxLodPixels>
      </Lod>
    </Region>
    """

    placemark = """
    <Placemark>
        <name>%s</name>
        <description>%s</description>
        <styleUrl>#default</styleUrl>
        %s
        %s
    </Placemark>
    """ 

    for kmlfile,values in kmls.items():
        if not kmz:
            fh = open(os.path.join(OUTDIR,kmlfile),'w')
        else:
            tmpfile = '/tmp/doc.kml'
            fh = open(os.path.join(tmpfile),'w')

        fh.write(kmlhead)
        levelnum, features = values
        level = LEVELS[levelnum]
        for feature in features:
            geom = feature['geom'].transform(4326,clone=True)
            uid = feature['uid']
            name = feature['name']
            desc = feature['desc']
            if level.simplify:
                geom = geom.geos.simplify(level.simplify)
            else:
                geom = geom.geos

            try:
                e = geom.extent
            except:
                print
                print geom
                continue

            if levelnum == len(LEVELS)-2:
                maxlod = "-1"
            else:
                maxlod = "1450"

            placemark_region = ""
            if levelnum == 0:
                placemark_region = region % (e[0],e[1],e[2],e[3])

            if not levelnum == len(LEVELS)-1:
                neturl = "%s%s.%s" % (URL,uid,extension)
                fh.write(netlink % (uid,
                                    e[0],e[1],e[2],e[3], #bbox
                                    maxlod,    
                                    neturl)
                )

            fh.write(placemark % (name,desc,geom.kml,placemark_region))

        fh.write(kmlfoot)
        fh.close()
        if kmz:
            outfile = os.path.join(OUTDIR,kmlfile)
            os.chdir('/tmp/')
            zip_file = zipfile.ZipFile(outfile, 'w', zipfile.ZIP_DEFLATED)
            zip_file.write('doc.kml')
            zip_file.close()

if __name__ == "__main__":
    kmls = {}
    drilldown(0,LEVELS)
    print kmls
    write_kmls(kmls)

OLCFG=seak_openlayers.cfg
OUTDIR=./openlayers_build
python build.py -c closure $OLCFG 
cp OpenLayers.js $OUTDIR 
cp -r ../theme $OUTDIR 
cp -r ../img $OUTDIR


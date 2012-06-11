OLCFG=nplcc.cfg
OUTDIR=/usr/local/src/nplcc/media/
#python build.py -c none $OLCFG
#python build.py $OLCFG 
python build.py -c closure $OLCFG 
cp OpenLayers.js $OUTDIR 
cp -r ../theme $OUTDIR 
cp -r ../img $OUTDIR


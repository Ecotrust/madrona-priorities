cd ../priorties/
pylint -d W0141,C0202,E1103,W0232,W0142,W0511,C0301,C0111,C0103,R \
    --generated-members=objects,lower,area,point_on_surface,all,strftime,DoesNotExist,add \
    --ignore=migrations \
    -i y \
    -f html \
    seak > lint.html

from django.core.management import setup_environ
import os
import sys
sys.path.append(os.path.dirname(__file__))

import settings
setup_environ(settings)

#==================================#
from arp.models import FocalSpecies as F

def main():
    L1 = F.objects.values_list('level1',flat=True).distinct()
    for val1 in L1:
        print val1
        L2 = F.objects.filter(level1=val1).values_list('level2',flat=True).distinct().exclude(level2=None)
        for val2 in L2:
            print " ", val2
            L3 = F.objects.filter(level2=val2).values_list('level3',flat=True).distinct().exclude(level3=None)
            for val3 in L3:
                print "  ", val3
                L4 = F.objects.filter(level3=val3).values_list('level4',flat=True).distinct().exclude(level4=None)
                for val4 in L4:
                    print "   ", val4

                    





if __name__ == '__main__':
    main()

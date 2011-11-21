"""
File	quantile.py
Desc	computes sample quantiles
Author  MMM modified from 
        program written by Ernesto P. Adorio, PhD.
		UPDEPP (U.P. at Clarkfield)

"""
from math import modf, floor
import math
import sys
import shapefile

char_arg = sys.argv[1]

def GetShpRecords(char,min_val):

	#-----------------------------------------------#
	#--------- This is one way to return -----------#
	#------ records for one field in a shp ---------#
	#-----------------------------------------------#

	#need to test if vars were passed
	#if min_val wasn't passed then set it to 0
	if min_val is None:
		min_val = 0
	print min_val
	q_sum = 0
	
	shp = './data/HUC8_WC20111021.shp'

	uidfield = 'huc_ref'
	field_num = 999

	#this is the field name where records will be returned
	#passed as an arg from whatever ap is calling the class
	#char = 'RD_DENS'

	#init the lists where (x) the records are stored and 
	#(fieldnames) where the field names are stored
	x = []
	fieldnames = []

	#load the shapefile
	print "Loading data from shapefile..."

	#return all fields and the number of fields to iterate through
	sf = shapefile.Reader(shp)
	fields = sf.fields
	field_cnt = len(fields)

	#return records and the number
	records = sf.records()
	recs = len(records)


	#now step through the fields to find the index 
	#of the one we're looking for (no doubt this could be
	#done a lot easier!)
	for n in range(0,field_cnt):
		fieldname = fields[n]
		fieldnames.append(fieldname[0])
		if fieldname[0] == char:
			field_num = n - 1
	
	#and step through the records to populate 
	#x list
	for i in range (0,recs):
		rowi = sf.record(i)
		t = rowi[field_num]
		x.append(float(t))
		if min_val > 0:
			if float(t) > min_val:
				q_sum += float(t)

	#print x
	return x, q_sum

	

	
	
def quantile(x, q,  qtype = 7, issorted = False):
	"""
	Args:
	   x - input data
	   q - quantile
	   qtype - algorithm
	   issorted- True if x already sorted.
	Compute quantiles from input array x given q.For median,
	specify q=0.5.
	References:
	   http://reference.wolfram.com/mathematica/ref/Quantile.html
	   http://wiki.r-project.org/rwiki/doku.php?id=rdoc:stats:quantile
	Author:
	Ernesto P.Adorio Ph.D.
	UP Extension Program in Pampanga, Clark Field.
	"""
	if not issorted:
		y = sorted(x)
	else:
		y = x
	if not (1 <= qtype <= 9):
	   return None  # error!
	# Parameters for the Hyndman and Fan algorithm
	abcd = [(0,   0, 1, 0), # inverse empirical distrib.function., R type 1
			(0.5, 0, 1, 0), # similar to type 1, averaged, R type 2
			(0.5, 0, 0, 0), # nearest order statistic,(SAS) R type 3
			(0,   0, 0, 1), # California linear interpolation, R type 4
			(0.5, 0, 0, 1), # hydrologists method, R type 5
			(0,   1, 0, 1), # mean-based estimate(Weibull method), (SPSS,Minitab), type 6
			(1,  -1, 0, 1), # mode-based method,(S, S-Plus), R type 7
			(1.0/3, 1.0/3, 0, 1), # median-unbiased ,  R type 8
			(3/8.0, 0.25, 0, 1)   # normal-unbiased, R type 9.
		   ]
	a, b, c, d = abcd[qtype-1]
	n = len(x)
	g, j = modf( a + (n+b) * q -1)
	if j < 0:
		return y[0]
	elif j >= n:
		return y[n-1]   # oct. 8, 2010 y[n]???!! uncaught  off by 1 error!!!
	j = int(floor(j))
	if g ==  0:
	   return y[j]
	else:
	   return y[j] + (y[j+1]- y[j])* (c + d * g)

x,sum = GetShpRecords(char_arg,0)  #getShpRecords returns multiple vars so each must be specified

def Test():
	#so what if we loaded a shapefile instead of the following array???
	#look to matt's code to see how he loads the data from a shape.
	
	#x = [4, 17.3, 18, 21.3, 25.9, 32, 40.1, 50.5, 51.4, 60.0, 70.0, 99, 100, 101, 102, 105, 462]
	
	for qtype in range(0,4):
		p = float(qtype) / 4
		print p, quantile(x, p, 1)  #(the list, the p_value, and the method)
if __name__ == "__main__":
	Test()
	#the next step is to take the top x quantile(s) and determine the sum of 
	#all values in that quantile. eg. if we have the .75 value = 3.2 and values of 
	#3.2,4.8,6.9 and 10.2 the sum = 25.1

	#to do this we step through the records and test to see if they're greater than
	#the specified quantile (in the p range above).

	#so the value of interest is the quantile of p or .75

	min_val = quantile(x, .75, 1)
	print "Our min val is " + str(min_val)
	
	x,sum = GetShpRecords(char_arg,min_val)
	print sum
	
	#so what we want then is a list of targets, each equal sum - we could return sum to the
	#annealing program - or execute the annealing program from a loop in this prog.
	
	


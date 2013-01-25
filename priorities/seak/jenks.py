"""
Jenks Natiural Breaks algorithm in python
http://danieljlewis.org/2010/06/07/jenks-natural-breaks-algorithm-in-python/
"""

def get_mats(dataList, numClass):
    mat1 = []
    for i in range(0,len(dataList)+1):
        temp = []
        for j in range(0,numClass+1):
            temp.append(0)
        mat1.append(temp)

    mat2 = []
    for i in range(0,len(dataList)+1):
        temp = []
        for j in range(0,numClass+1):
            temp.append(0)
        mat2.append(temp)

    for i in range(1,numClass+1):
        mat1[1][i] = 1
        mat2[1][i] = 0
        for j in range(2,len(dataList)+1):
            mat2[j][i] = float('inf')

    return mat1, mat2

def get_jenks_breaks( dataList, numClass ):
    if len(dataList) == 0:
        raise Exception("dataList passed to get_jenks_breaks was empty")
    elif len(dataList) == 1:
        dataList *= 2 # need at least two elements in list

    dataList.sort()

    mat1, mat2 = get_mats(dataList, numClass)

    v = 0.0
 
    class_range = range(2, numClass+1)
    for x in range(2,len(dataList)+1):
        s1 = 0.0
        s2 = 0.0
        w = 0.0
        for m in range(1,x+1):
            i3 = x - m + 1
            val = float(dataList[i3-1])
            s2 += val * val
            s1 += val
            w += 1
            v = s2 - (s1 * s1) / w
            i4 = i3 - 1
            if i4 != 0:
                for j in class_range: 
                    if mat2[x][j] >= (v + mat2[i4][j - 1]):
                        mat1[x][j] = i3
                        mat2[x][j] = v + mat2[i4][j - 1]
        mat1[x][1] = 1
        mat2[x][1] = v

    k = len(dataList)
    kclass = []
    for i in range(0,numClass+1):
        kclass.append(0)

    kclass[numClass] = float(dataList[len(dataList) - 1])

    countNum = numClass
    while countNum >= 2:
        id = int((mat1[k][countNum]) - 2)

        kclass[countNum - 1] = dataList[id]
        k = int((mat1[k][countNum] - 1))
        countNum -= 1

    return kclass

def getGVF( dataList, numClass ):
    """
    The Goodness of Variance Fit (GVF) is found by taking the 
    difference between the squared deviations
            from the array mean (SDAM) and the squared deviations from the 
    class means (SDCM), and dividing by the SDAM
    """
    breaks = getJenksBreaks(dataList, numClass)
    dataList.sort()
    listMean = sum(dataList)/len(dataList)
    SDAM = 0.0
    for i in range(0,len(dataList)):
        sqDev = (dataList[i] - listMean)**2
        SDAM += sqDev
    SDCM = 0.0
    for i in range(0,numClass):
        if breaks[i] == 0:
            classStart = 0
        else:
            classStart = dataList.index(breaks[i])
            classStart += 1

        classEnd = dataList.index(breaks[i+1])
        classList = dataList[classStart:classEnd+1]
        classMean = sum(classList)/len(classList)

        preSDCM = 0.0
        for j in range(0,len(classList)):
            sqDev2 = (classList[j] - classMean)**2
            preSDCM += sqDev2

        SDCM += preSDCM
    return (SDAM - SDCM)/SDAM

if __name__ == '__main__':
    import random
    dataset = sorted([float(random.randint(0,100)) for r in xrange(75)])
    #print get_jenks_breaks(dataset, 4)

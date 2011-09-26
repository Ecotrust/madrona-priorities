cdef extern from "stdlib.h":         
    long rand()                    
    void srand(int seed)                    

cdef extern from "time.h":
    ctypedef long time_t
    time_t time(time_t*)

srand(time(NULL))

def c_random_int(int max):
    return int(rand() % max)

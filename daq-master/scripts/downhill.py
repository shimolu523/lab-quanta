#coding=utf8
# 2010-05-24
# Hans Harhoff Andersen
# Downhill simplex - downhill.py
import numpy as np
import math
import sys
import __main__
#import matplotlib.pyplot as plt

def amoeba(F,s,acc):
	# s shold be n+1 times n array
	# as there are n+1 points each with n coordinates
	s=s.astype(float)
	p=s[0]
	n=len(p)
	fs=np.zeros(n+1)
        try:
	    for i in range(n+1):
	        	fs[i]=F(s[i])
        except Exception,e:
            print "Exception occured in downhill.amoeba while F and s[i]",e
            print "i=%d, n=%d"%(i,n)
            print "fs=",fs
            print "s",s
            raise e
	k=0
        try:
            while size(s)>acc:
                    if __main__.STOP_FLAG: break
                    # Find highest, lowest and centroid points:
                    h=0
                    l=0
                    for i in range(len(fs)):
                            if fs[i]>fs[h]: h=i
                            if fs[i]<fs[l]: l=i
                    pce=(np.sum(s,0)-s[h])/n
                    phi=s[h]
                    pre=pce+(pce-phi)
                    pex=pce+2*(pce-phi)
                    # Try reflection:
                    Fre=F(pre)
                    if Fre<fs[h]:
                            # Accept reflection
                            s[h]=pre
                            fs[h]=Fre
                            if Fre<fs[l]:
                                    # Try expansion
                                    Fex=F(pex)
                                    if Fex<Fre:
                                            # Accept expansion
                                            s[h]=pex
                                            fs[h]=Fex
                    else:
                            pco=pce+0.5*(phi-pce)
                            # Try contraction:
                            Fco=F(pco)
                            if Fco<fs[h]:
                                    # Accept contraction:
                                    s[h]=pco
                                    fs[h]=Fco
                            else:
                                    # Do reduction:
                                    for i in range(len(s)):
                                            if i!=l:
                                                    s[i]=0.5*(s[i]+s[l])
                                                    fs[i]=F(s[i])
                                    print "Reduction"
                    k=k+1
                    # Code for plotting the simplex routine and making a little movie of it!
                    #plt.fill(s[:,0],s[:,1])
                    #filename="animation/downhill"+str(k).zfill(3)+".png"
                    #plt.savefig(filename,format="png")
                    # End of while! While runs until we meet the accuracy goal!
        except Exception,e:
                print "Exception occured in downhill.amoeba in while loop:",e
                raise e

	if __main__.STOP_FLAG==False:
	    return s[l]
        else:
            return None
def size(s):
	n=len(s[0])
	dists=np.zeros(n)
	for i in range(1,n):
		dists[i]=dist(s[i],s[0])
	return np.linalg.norm(dists)

def dist(a_s,b_s):
	return 	np.linalg.norm(a_s-b_s)


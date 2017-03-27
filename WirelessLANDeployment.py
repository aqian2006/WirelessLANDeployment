##!/usr/bin/env python

# import modules used here -- sys is a very standard one
import sys
#import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import utility
from operator import itemgetter, attrgetter
import random
import time
import os
import math


def params_def_init():
    # This function read parameters from parameters from parameters.ini file
    # and define the corresponding global variables
	utility.log_info("Enter params_def_init()")
	parmfilename = os.path.join(utility.get_current_dir(),"parameters.ini")
	if os.path.isfile(parmfilename) == False:
		log_error("parameters.ini file is not exist!")
		return False
	utility.log_info("------Parameters from ini file------")
	parmfile = open(parmfilename,"r")
	line = parmfile.readline()
	while line:
		stripeline = line.strip()
		if ( stripeline[0:1] == "#" ):
        #skip the comment line with "#" in the head of the line
			line = parmfile.readline()
			continue
		key_value = stripeline.split("#")[0].split("=")
		if ( len(key_value) >= 2 ):
			globals()[key_value[0].strip()] = float(key_value[1].strip())
            #define the global variables, the value is asummed as float type
			utility.log_info("\t\t"+key_value[0].strip()+"\t=\t"+key_value[1].strip())
		line = parmfile.readline()
	parmfile.close()
	utility.log_info("------------End------------")


class TargetArea(object):

    def __init__(self):
        self._width          =   g_area_width
        self._length         =   g_area_width
        self._user_density   =   g_user_density
        self._M              =   int(g_M)
        self._gamma          =   g_gamma
#        self._listD          =   [20,30,40,50,220,225,230]#randomDm0()
        self._listD          =   np.random.uniform(20,640,self._M)#self.randomDm0()# [20,30,40,50,220,225,230]#randomDm0()
        #self._gm             =   g_gm
        self._L              =   self._listD.sum() #g_L

    def randomDm0(self):
        self._listD          = np.random.uniform(20,600,self._M)

    def demandDm0(self,i):
        if i < 0 or i >= self.M:
            print "[ERROR]: ", i, " is out of range"

        return self._listD[i]

    def gamma(self,i):

        return self._gamma

    def M(self):
        if self._M <= 0:
            print "[ERROR] The candidate AP locations should be greater than 0: ", self.M
        return int(self._M)

    def L(self):

        return self._L

    def potential_demand_total(self):

        return self._listD.sum()

    def save_potential_demand(self):
        demand_avg = self.potential_demand_total()/self.M()
        filename="potential-demand("+str(self._M)+").csv"
        utility.create_output_file(filename)
        utility.save_to_output("Location No., Potential Demand(GB), Average Demand(GB)")

        for i in range(self.M()):
            utility.save_to_output(str(i+1)+","+str(self._listD[i])+","+str(demand_avg))

        utility.close_output_file()

class Demand(object):
    def __init__(self, Dm0, gamma):
        self.Dm0        =   Dm0
        self.gamma      =   gamma

    def demand(self, pw):
        return self.Dm0 - self.gamma * pw

class DeployAgent(object):
    def __init__(self, targetArea):
        self.targetArea         =  targetArea
        self._pc                =  g_pc
        self._hc                =  g_hc
        self._hw                =  g_hw
        self._pw                =  None
        self._demand_ap_total   =  None
        self._profit_ap_total     =  None
        self._demand_c_total      =  None
        self._profit_c_total      =  None
        self._gm                =  g_gm
        self._list_is_deploy    =  np.zeros(self.targetArea.M())
        self._mode              =  0 # 0-optimal, 1- random

    def gm(self,i):

        return self._gm

    def reset(self):
        self._pw                =  None
        self._demand_ap_total   =  None
        self._profit_ap_all     =  None
        self._demand_c_all      =  None
        self._profit_c_all      =  None
        self._list_is_deploy    =  np.zeros(self.targetArea.M())

    def set_mode(self,m):

        self._mode = m

    def set_gm(self,new_gm):
        self._gm = new_gm

    def optimal_pw(self,i):

        self._pw = self.targetArea.demandDm0(i) / (2*self.targetArea.gamma(i)) \
               + (self._hw + self._pc - self._hc) / 2

        return self._pw

    def demand_ap(self, i):
        self.optimal_pw(i)

        return self.is_deploy_ap(i)*(self.targetArea.demandDm0(i)-self.targetArea.gamma(i) * self._pw)

    def demand_ap_total(self):
        self._demand_ap_total = 0
        for i in range(self.targetArea.M()):
            self._demand_ap_total += self.demand_ap(i)

        return self._demand_ap_total

    def demand_cellular(self):
        self._demand_c_total = self.targetArea.L() - self.demand_ap_total()

        return self._demand_c_total

    def is_deploy_ap(self,i):
        if self._mode == 0:
            return self.is_deploy_optimal(i)

        return self.is_deploy_random(i)

    def is_deploy_optimal(self,i):
        a = self.targetArea.demandDm0(i) / (2*np.sqrt(self.targetArea.gamma(i))) \
               + np.sqrt(self.targetArea.gamma(i)) * (self._hc-self._pc-self._hw) / 2
        b = np.sqrt(self.gm(i))
        if a > b:
            self._list_is_deploy[i] = 1
        return  self._list_is_deploy[i]

    def is_deploy_random(self,i):
        return self._list_is_deploy[i]

    def profit_ap(self,i):
        return self.is_deploy_ap(i) * ( self.demand_ap(i) * (self._pw-self._hw) \
                                        - self.gm(i) )
    def profit_ap_total(self):
        self._profit_ap_total = 0
        for i in range(self.targetArea.M()):
            self._profit_ap_total += self.profit_ap(i)

        return self._profit_ap_total

    def profit_c_total(self):

        self._profit_c_total = self.demand_cellular()*(self._pc - self._hc)

        return  self._profit_c_total

    def profit_total(self):

        return self.profit_ap_total() + self.profit_c_total()

    def profit_baseline(self):

        return self.targetArea.potential_demand_total() * (self._pc - self._hc)

    def num_of_aps(self):
        return self._list_is_deploy.sum()

    def list_is_deploy(self):

        return self._list_is_deploy

    def randomize_deploy_list(self):
        np.random.shuffle(self._list_is_deploy)


class DeployerOptimal(DeployAgent):
    def __init__(self, policy, route=0):
        self.a=0

    def setk(self):
        return 0

def ProfitWithDiffDeploymentCost():

    ta = TargetArea()
    ta.save_potential_demand()

    dp = DeployAgent(ta)
#    print ta.demandDm0(1)
#    print ta.gamma(1)

#    listG = []

    utility.create_output_file()
    utility.save_to_output("depl-cost," + "profit-baseline,"+"profit-optimal,"+"profit-random,"+"off-traf-opti," + "cell-traf-opti," + "off-traf-rand," + "cell-traf-rand,"+"num-of-APs")

    profit_baseline = dp.profit_baseline()
    for gm in range(0,20000,1000):
        dp.reset()
        dp.set_gm(gm)
        dp.set_mode(0)
        profit_optimal = dp.profit_total()
        d_ap      = dp.demand_ap_total()
        d_cellular= dp.demand_cellular()
        print "profit optimal:", profit_optimal

#        print "aps deployed optimal:", dp.list_is_deploy()
        dp.randomize_deploy_list()
#        print "aps deployed random:", dp.list_is_deploy()
        dp.set_mode(1)
        profit_random = dp.profit_total()

        print "profit random:", profit_random
        d_ap_r       = dp.demand_ap_total()
        d_cellular_r = dp.demand_cellular()
        utility.save_to_output(str(gm)+","+str(profit_baseline)+","+str(profit_optimal)+","+str(profit_random)\
                +","+str(d_ap)+","+str(d_cellular) +","+str(d_ap_r)+","+str(d_cellular_r)\
                +","+str(dp.num_of_aps()))

    utility.close_output_file()
    utility.close_log_file()

def main():
#    global g_switch_of_known_consumption, g_switch_of_unknown_consumption
    print '\n============================================================='
    print '\n\tThis is Markov Decision Process Simulation Program!'
    print '\n\tAuthor: Cheng ZHANG'
    print '\n\t  Date: 2016/12/17'
    print '\n============================================================='
    utility.init_log_file("log.log")
    utility.log_info("Enter function: "+main.__name__)
##    utility.create_output_file()
##
    if ( params_def_init() is False ):
        utility.log_error("Fail to initialize parameters, abort the program")
        print "[ERROR] Fail to initialize parameters, abort the program, see log.log file for detail information."
        utility.close_log_file()
        return
#    utility.close_log_file()


    ProfitWithDiffDeploymentCost()
  #  print "potentaial demand total:", ta.potential_demand_total()
#        print "aps deployed:", dp.list_is_deploy()
#        print "num of aps:", dp.num_of_aps()
#        print "aps shuffled:", dp.list_random_is_deploy()
#        print "aps deployed:", dp.list_is_deploy()
#        print "num of aps:", dp.num_of_aps()
#    for i in range(7):
#        print dp.profit_ap(i)

#    p2 = dp.profit_ap_total()
#    p3 = dp.demand_c_total()
#    p1 = dp.profit_c_total()
#    p3 = dp.profit_total()

#    print p2
#    print p1
#    print p3
#    print "location and Cellular throughput\n",g_Cellular_Throughput,"\n"
#    utility.log_info("Randomly generated WiFi throughput ( location : WiFi throughput(Mbps) )\n\t\t"
#					+str(g_WiFi_Throughput))
#    utility.log_info("Randomly generated cellular throughput ( location : cellular throughput(Mbps) )\n\t\t"
#					+str(g_Cellular_Throughput))


if __name__ == '__main__':
    main()


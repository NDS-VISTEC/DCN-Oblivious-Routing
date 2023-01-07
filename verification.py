# Copyright (c) 2023 VISTEC - Vidyasirimedhi Institute of Science and Technology
# Distribute under MIT License
# Authors:
#  - Sucha Supittayapornpong <sucha.s[-at-]vistec.ac.th>
#  - Kanatip Chitavisutthivong <kanatip.c_s18[-at-]vistec.ac.th>

import os
import pickle
import networkx as nx
import gurobipy as gp
import multiprocessing as mp

import state_helper as helper
from state_helper import HCONST

from topology_automorphism import applyGenerator


class Verification:
    """
    Class Verification for verify the optimal solution from Optimization process

    ...

    Attributes
    ----------
    toponame : str
        a topology name 
    numThread : int
        a number of thread (default 1)
    intermediate : bool
        is the intermediate solution (default False)
    Topo : Topology
        Topology object
    Route : dict
        a solution route

    """

    def __init__(self, toponame, numThread=1, intermediate=False):
        self.toponame = toponame
        self.numThread = numThread
        self.intermediate = intermediate

        print('-------------------------')
        print('Step: Solution Verification')
        print('-------------------------')

        rootdir = '.'
        helper.initHCONST(rootdir, toponame)
        self.Topo = pickle.load(open(HCONST['outputpath'] + '/' + 'Topology', 'rb'))
        if self.intermediate is False:
            self.Route = pickle.load(open(HCONST['outputpath'] + '/' + 'OptimalRouting', 'rb'))
        else:
            self.Route = pickle.load(open(HCONST['outputpath'] + '/' + 'IntermediateSolution', 'rb'))

        
    def verifyAllLinkLoad(self):
        if os.path.exists(HCONST['outputpath'] + '/' + 'VerifiedThroughput'):
            verifiedThroughput = pickle.load(open(HCONST['outputpath'] + '/' + 'VerifiedThroughput', 'rb'))
            print('\t Verified: Max link load =', 1.0/verifiedThroughput)
            print('\t Verified: Throughput =', verifiedThroughput)
            return

        linkload = dict()        
        pool = mp.Pool(self.numThread)
        for link, maxload in pool.imap_unordered(self.findMaxLinkLoad, self.Topo.DLinks):
            linkload[link] = maxload/self.Topo.UG.get_edge_data(*link)['capacity']
        pool.close()
        pool.join()                    

        maxload = max(linkload.values())
        verifiedThroughput = 1.0/maxload
        if self.intermediate is False:
            pickle.dump(verifiedThroughput, open(HCONST['outputpath'] + '/' + 'VerifiedThroughput', 'wb'))
            print('\t Verified: Max link load =', maxload)
            print('\t Verified: Throughput =', verifiedThroughput)            
        else:
            pickle.dump(verifiedThroughput, open(HCONST['outputpath'] + '/' + 'VerifiedIntermediateThroughput', 'wb'))
            print('\t Verified Intermediate: Max link load =', maxload)
            print('\t Verified Intermediate: Throughput =', verifiedThroughput)
            
        return maxload, verifiedThroughput

    
    def findMaxLinkLoad(self, link):
        Topo = self.Topo
        Route = self.Route
        
        m = gp.Model()
        m.setParam('OutputFlag', 0)

        p = m.addVars(Topo.Commodities, vtype=gp.GRB.CONTINUOUS, name='p')

        for n in Topo.HostNodes:
            numServer = Topo.UG.nodes[n]['numServer']
            m.addConstr(p.sum(n, '*') <= numServer, name='o_{0}'.format(n))
            m.addConstr(p.sum('*', n) <= numServer, name='i_{0}'.format(n))

        m.update()            

        load = 0
        for repsd in Topo.RepCommodities:
            autcomms = Topo.loadCommodityGroup(repsd)
            for sd in autcomms:
                rmap = Topo.loadCommodityAutomorphicMap(sd, isForward=False)
                alink = applyGenerator(link, rmap)
                if repsd in Route.get_edge_data(*alink).keys():
                    load += p[sd] * Route.get_edge_data(*alink)[repsd]

        m.setObjective(load, sense=gp.GRB.MAXIMIZE)

        m.optimize()
        assert m.status == gp.GRB.OPTIMAL
        return (link, m.ObjVal)

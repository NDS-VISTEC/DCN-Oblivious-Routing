# Copyright (c) 2023 VISTEC - Vidyasirimedhi Institute of Science and Technology
# Distribute under MIT License
# Authors:
#  - Sucha Supittayapornpong <sucha.s[-at-]vistec.ac.th>
#  - Kanatip Chitavisutthivong <kanatip.c_s18[-at-]vistec.ac.th>

import networkx as nx
import pickle
import os

import gurobipy as gp
import multiprocessing as mp

from state_helper import HCONST
import network_generator as netgen

class SlimFlyRouting:
    """
    Class SlimFlyRouting for generating Slimfly's VAL route based on 

    M. Besta and T. Hoefler, “Slim fly: A cost effective low-diameter network topology,” in SC '14:
    Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis, 2014, pp. 348-359.

    ...

    Attributes
    ----------
    Topo : Topology
        Topology object 
    H : nx.Graph
        a directed graph
    numNode : int
        a number of nodes
    Route : dict
        Slimfly route

    """

    def __init__(self, topo, numThread=1):
        self.Topo = topo
        self.H = self.Topo.UG.to_directed()
        self.numNode = self.H.number_of_nodes()

        self.Route = None
            
        if not os.path.exists(HCONST['outputpath'] + '/' + 'VALRouting'):
            print("VAL route does not exist")
            print("Generate VAL route")
            self.generateVALRoute(numThread)
        else:
            print("Load VAL route")
            self.Route = pickle.load(open(HCONST['outputpath'] + '/' + 'VALRouting', 'rb'))


    def getMIN(self, src, dst):
        path = nx.shortest_path(self.H, source=src, target=dst)
        return path


    def getVAL(self, src, dst, imm):
        pathA = self.getMIN(src, imm)
        pathB = self.getMIN(imm, dst)
        pathA.remove(imm)
        return pathA + pathB


    def getVALpaths(self, src, dst):
        nodes = list(range(self.numNode))
        nodes.remove(src)
        nodes.remove(dst)
        paths = list()
        for imm in nodes:
            path = self.getVAL(src, dst, imm)
            paths.append(path)
        return paths


    def toEdgesPath(self, path):
        paths = list()
        for i in range(len(path)-1):
            nodeA = path[i]
            nodeB = path[i+1]
            paths.append((nodeA,nodeB))
        return paths


    def generateVALRoute(self, numThread):
        VALRoute = dict()
        pool = mp.Pool(numThread)
        for VALRoute_sd, sd in pool.imap_unordered(self.generateVALRouteSub, self.Topo.Commodities):
            VALRoute[sd] = VALRoute_sd
        pool.close()
        pool.join()

        self.Route = VALRoute
        pickle.dump(VALRoute, open(HCONST['outputpath'] + '/' + 'VALRouting', 'wb'))


    def generateVALRouteSub(self, sd):

        VALRoute_sd = dict()
        src, dst = sd
        paths = self.getVALpaths(src, dst)
        flow = 1.0/(self.numNode-2)
        for p in paths:
            p = self.toEdgesPath(p)
            for edge in p:
                if edge in VALRoute_sd:
                    VALRoute_sd[edge] += flow
                else:
                    VALRoute_sd[edge] = flow
        
        return VALRoute_sd, sd


    def verifyAllLinkLoad(self, numThread):
        if os.path.exists(HCONST['outputpath'] + '/' + 'VerifiedThroughputSlimflyVAL'):
            verifiedThroughput = pickle.load(open(HCONST['outputpath'] + '/' + 'VerifiedThroughputSlimflyVAL', 'rb'))
            print('Verified: Max link load =', 1.0/verifiedThroughput)
            print('Verified: Throughput =', verifiedThroughput)
            return

        linkload = dict()
        pool = mp.Pool(numThread)
        for link, maxload in pool.imap_unordered(self.findMaxLinkLoad, self.Topo.DLinks):
            linkload[link] = maxload/self.Topo.UG.get_edge_data(*link)['capacity']
        pool.close()
        pool.join()

        maxload = max(linkload.values())
        verifiedThroughput = 1.0/maxload
        print('Verified: Max link load =', maxload)
        print('Verified: Throughput =', verifiedThroughput) 
        pickle.dump(verifiedThroughput, open(HCONST['outputpath'] + '/' + 'VerifiedThroughputSlimflyVAL', 'wb'))     
        return maxload, verifiedThroughput


    def findMaxLinkLoad(self, link):

        m = gp.Model()
        m.setParam('OutputFlag', 0)

        p = m.addVars(self.Topo.Commodities, vtype=gp.GRB.CONTINUOUS, name='p')

        for n in self.Topo.HostNodes:
            numServer = self.Topo.UG.nodes[n]['numServer']
            m.addConstr(p.sum(n, '*') <= numServer, name='o_{0}'.format(n))
            m.addConstr(p.sum('*', n) <= numServer, name='i_{0}'.format(n))

        m.update()            

        load = 0
        for sd in self.Topo.Commodities:
            if link in self.Route[sd]:
                load += p[sd] * self.Route[sd][link]
        m.setObjective(load, sense=gp.GRB.MAXIMIZE)
        m.optimize()
        assert m.status == gp.GRB.OPTIMAL
        return (link, m.ObjVal)



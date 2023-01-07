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


class BCubeRouting:
    """
    Class BCubeRouting for generating BCube's route based on 

    C. Guo, G. Lu, D. Li, H. Wu, X. Zhang, Y. Shi, C. Tian, Y. Zhang, S. Lu, and G. Lv, 
    “Bcube: A high performance, server-centric network architecture for modular data centers,” in ACM SIGCOMM. 
    Association for Computing Machinery, Inc., August 2009.

    ...

    Attributes
    ----------
    K : int
        a parameter of BCube topology
    numPort : int
        a parameter of BCube topology (a number of ports on a switch)
    Topo : Topology
        Topology object 
    mappingAddrToBaddr : dict
        a mapping from node-id to BCube address
    mappingBaddrToAddr : dict
        a mapping from BCube address to node-id
    Route : dict
        BCute route

    """

    def __init__(self, K, numPort, mappingAddrToBaddr, mappingBaddrToAddr, topo):
        self.K = K
        self.numPort = numPort
        self.Topo = topo
        self.mappingAddrToBaddr = mappingAddrToBaddr
        self.mappingBaddrToAddr = mappingBaddrToAddr

        self.Route = None
            
        if not os.path.exists(HCONST['outputpath'] + '/' + 'BCubeRouting'):
            print("BCube route does not exist")
            print("Generate BCube route")
            self.generateBCubeRoute()
        else:
            print("Load BCube route")
            self.Route = pickle.load(open(HCONST['outputpath'] + '/' + 'BCubeRouting', 'rb'))


    def BcubeRouting(self, addrA, addrB, pi, K):
        path = [addrA]
        i_node = list(addrA)

        for i in range(K+1):    # i = [0, 1, ... , K]
            if addrA[pi[i]] != addrB[pi[i]]:
                i_node[pi[i]] = addrB[pi[i]]
                path.append(tuple(i_node))
        return path


    def getNeighbors(self, addrA, level, K, numPort):
        addrA = list(addrA)
        neighbors = list()
        for i in range(numPort):
            addr = addrA.copy()
            addr[level] = i
            if addr[level] != addrA[level]:
                neighbors.append(tuple(addr))
        return neighbors


    def buildPathSet(self, addrA, addrB):
        K = self.K
        numPort = self.numPort
        paths = list()
        pi = list(range(K+1))

        for i in range(K+1):    # i = [0, 1, ... , K]
            if addrA[i] != addrB[i]:
                p_i = self.dcRouting(addrA, addrB, i, K, pi)
                paths.append(p_i)
            else:
                neighbors = self.getNeighbors(addrA, i, K, numPort)
                for j in range(len(neighbors)):
                    addrC = neighbors[j]
                    p_i = self.altdcRouting(addrA, addrB, i, K, addrC, pi)
                    paths.append(p_i)
        return paths


    def dcRouting(self, addrA, addrB, i, K, pi):
        m = 0 
        j = i
        while (j >= i - K):
            pi[m] = j % (K+1)
            m = m + 1
            j-=1
        path = self.BcubeRouting(addrA, addrB, pi, K)
        return path


    def altdcRouting(self, addrA, addrB, i, K, addrC, pi):
        path = [addrA]
        m = 0
        j = i - 1
        while (j >= i - 1 - K):
            pi[m] = j % (K+1)
            m = m + 1
            j-=1
        path.extend(self.BcubeRouting(addrC, addrB, pi, K))
        return path


    def getPathEdgesIntermediateSwitch(self, addrA, addrB):
        Topo = self.Topo

        def getImmSW(swAs, swBs):
            immSW = list(set(swAs) & set(swBs))
            return immSW[0]

        def getswList(edges):
            swList = list()
            for i in range(len(edges)):
                swList.append(edges[i][1])
            return swList
        
        edgesA = list(Topo.UG.edges(addrA))
        swAs = getswList(edgesA)
        edgesB = list(Topo.UG.edges(addrB))
        swBs = getswList(edgesB)
        immSW = getImmSW(swAs, swBs)

        pathEdges = list()
        for i in range(len(edgesA)):
            swA = edgesA[i][1]
            swB = edgesB[i][1]
        
            if swA == immSW:
                pathEdges.append(edgesA[i])
            if swB == immSW:
                reverse_edgeB = (edgesB[i][1], edgesB[i][0])
                pathEdges.append(reverse_edgeB)

        return pathEdges


    def getPathEdges(self, path):
        mappingAddrToBaddr = self.mappingAddrToBaddr

        pathEdges = list()
        for i in range(len(path)-1):
            addrA = mappingAddrToBaddr[path[i]]
            addrB = mappingAddrToBaddr[path[i+1]]
            pathEdgesImmSW = self.getPathEdgesIntermediateSwitch(addrA, addrB)
            pathEdges.extend(pathEdgesImmSW)
        return pathEdges


    def generateBCubeRoute(self):
        Topo = self.Topo
        mappingBaddrToAddr = self.mappingBaddrToAddr

        BcubeRoute = dict()
        for c in Topo.Commodities:
            BcubeRoute[c] = dict()
            addrSrc, addrDst = c
            addrSrc = mappingBaddrToAddr[addrSrc]
            addrDst = mappingBaddrToAddr[addrDst]
            paths = self.buildPathSet(addrSrc, addrDst)
            flow = 1.0/len(paths)
            for p in paths:
                pathEdges = self.getPathEdges(p)
                for edge in pathEdges:
                    if edge in BcubeRoute[c]:
                        BcubeRoute[c][edge] += flow
                    else:
                        BcubeRoute[c][edge] = flow
        
        self.Route = BcubeRoute
        pickle.dump(BcubeRoute, open(HCONST['outputpath'] + '/' + 'BCubeRouting', 'wb'))


    def verifyAllLinkLoad(self, numThread=1):
        Topo = self.Topo

        if os.path.exists(HCONST['outputpath'] + '/' + 'VerifiedThroughputBCube'):
            verifiedThroughput = pickle.load(open(HCONST['outputpath'] + '/' + 'VerifiedThroughputBCube', 'rb'))
            print('Verified: Max link load =', 1.0/verifiedThroughput)
            print('Verified: Throughput =', verifiedThroughput)
            return

        linkload = dict()
        pool = mp.Pool(numThread)
        for link, maxload in pool.imap_unordered(self.findMaxLinkLoad, Topo.DLinks):
            linkload[link] = maxload/Topo.UG.get_edge_data(*link)['capacity']
        pool.close()
        pool.join()

        maxload = max(linkload.values())
        verifiedThroughput = 1.0/maxload
        print('Verified: Max link load =', maxload)
        print('Verified: Throughput =', verifiedThroughput)
        pickle.dump(verifiedThroughput, open(HCONST['outputpath'] + '/' + 'VerifiedThroughputBCube', 'wb'))    
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
        for sd in Topo.Commodities:
            if link in Route[sd]:
                load += p[sd] * Route[sd][link]
        m.setObjective(load, sense=gp.GRB.MAXIMIZE)
        m.optimize()
        assert m.status == gp.GRB.OPTIMAL
        return (link, m.ObjVal)


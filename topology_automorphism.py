# Copyright (c) 2023 VISTEC - Vidyasirimedhi Institute of Science and Technology
# Distribute under MIT License
# Authors:
#  - Sucha Supittayapornpong <sucha.s[-at-]vistec.ac.th>
#  - Kanatip Chitavisutthivong <kanatip.c_s18[-at-]vistec.ac.th>

import networkx as nx
import pynauty
import itertools
import pickle
import time
import os
import multiprocessing as mp


import state_helper as helper
from state_helper import HCONST


def involve(node, autmap):
    return autmap[node] != node


def applyGenerator(nodes, autmap):
    """ Apply a automorphic generator function

        Parameters
        ----------
        nodes : tuple
            a tuple of nodes
        autmap : list
            a automorphic generator function
        
        Returns:
        ----------
           automorphic nodes: tuple
            a tuple of automorphic nodes
    """       
    return tuple(autmap[n] for n in nodes)


class Topology:
    """
    Topology class 

    ...

    Attributes
    ----------
    Name : str
        a topology name 
    NumThread : int
        a number of thread
    UG : nx.Graph
        a undirecteed graph
    RouteNodes : set
        a set of routing-capable nodes
    NonRouteNodes : set
        a set of routing-incapable nodes
    AllNodes : set
        a set of all nodes
    HostNode : set
        a set of nodes that have positive node capacities
    Commodities : set
        a set of commodities
    ULinks : set
        a set of undirected links
    DLinks : set
        a set of directed links
    Autgen : set
        a set of automorphic generators
    RepCommodities : set
        a set of representative commodities    
    RepCommFlowLinks : set
        a set of representative flow links    
    RepAuxiliarys : set
        a set of representative auxiliarys    
    RepLinkConstrs : set
        a set of representative link constraints        
    ComputationTime : dict
        store compupation times   
    """

    def __init__(self, ugraph, toponame, numThread=1):
        self.Name = toponame
        self.NumThread = numThread
        self.UG = None
        self.RouteNodes = None
        self.NonRouteNodes = None
        self.AllNodes = None
        self.HostNode = None
        self.Commodities = None
        self.ULinks = None
        self.DLinks = None
        self.Autgen = None
        self.RepCommodities = None
        self.RepCommFlowLinks = None
        self.RepAuxiliarys = None
        self.RepLinkConstrs = None
        self.ComputationTime = dict()

        print('-------------------------')
        print('Step: Topology Automorphism')
        print('-------------------------')

        self.setUGraph(ugraph)

        print('\t Find generators: ', end='')
        cnttime = time.time()
        self.findAutomorphicGenerators()
        cnttime = time.time() - cnttime
        print('{0:.2f}'.format(cnttime))
        self.ComputationTime['Find generators'] = cnttime
        
        print('\t Find representative commodities: ', end='')
        cnttime = time.time()
        self.findRepresentativeCommodities()
        cnttime = time.time() - cnttime
        print('{0:.2f}'.format(cnttime))
        self.ComputationTime['Find representative commodities'] = cnttime

        print('\t Find representative flow links: ', end='')
        cnttime = time.time()
        self.findRepresentativeCommodityFlowLinks()
        cnttime = time.time() - cnttime
        print('{0:.2f}'.format(cnttime))
        self.ComputationTime['Find representative flow links'] = cnttime

        print('\t Find representative auxs: ', end='')
        cnttime = time.time()
        self.findRepresentativeAuxs()
        self.computeAuxReverseMap()
        cnttime = time.time() - cnttime
        print('{0:.2f}'.format(cnttime))
        self.ComputationTime['Find representative auxs'] = cnttime

        print('\t Find representative link constraints: ', end='')
        cnttime = time.time()
        self.findRepresentativeLinkConstrs()
        cnttime = time.time() - cnttime
        print('{0:.2f}'.format(cnttime))
        self.ComputationTime['Find representative link constraints'] = cnttime

        pickle.dump(self.ComputationTime, open(HCONST['outputpath'] + '/' + 'TopoComputationTime', 'wb'))
        
        
    def setUGraph(self, ugraph):
        stagepath = HCONST['stagepath'] + '/' + 'setUGraph'
        if os.path.exists(stagepath):
            (self.UG, self.RouteNodes, self.NonRouteNodes, self.AllNodes, self.HostNodes, self.Commodities, self.ULinks, self.DLinks) = pickle.load(open(stagepath, 'rb'))
            return
        
        assert set(ugraph.nodes()) == set(range(ugraph.number_of_nodes()))
        self.UG = nx.Graph()
        for n in ugraph.nodes():
            numServer = ugraph.nodes[n]['numServer']
            routeCap = ugraph.nodes[n]['routing']
            self.UG.add_node(n, numServer=numServer, routing=routeCap)

        for e in ugraph.edges():
            capacity = ugraph.edges[e]['capacity']
            self.UG.add_edge(*e, capacity=capacity)

        self.RouteNodes = set([n for n in self.UG.nodes() if self.UG.nodes[n]['routing'] == True])            
        self.NonRouteNodes = set([n for n in self.UG.nodes() if self.UG.nodes[n]['routing'] == False])
        self.AllNodes = self.RouteNodes.union(self.NonRouteNodes)
        self.HostNodes = set([n for n in self.UG.nodes() if self.UG.nodes[n]['numServer'] > 0])
        self.Commodities = set(itertools.permutations(self.HostNodes, 2))        
        self.ULinks = set(self.UG.edges())
        self.DLinks = self.ULinks.union([(j, i) for (i, j) in self.ULinks])

        stagedata = (self.UG, self.RouteNodes, self.NonRouteNodes, self.AllNodes, self.HostNodes, self.Commodities, self.ULinks, self.DLinks)
        pickle.dump(stagedata, open(stagepath, 'wb'))


    def findAutomorphicGenerators(self):
        stagepath = HCONST['stagepath'] + '/' + 'findAutomorphicGenerator'
        if os.path.exists(stagepath):
            (self.Autgen) = pickle.load(open(stagepath, 'rb'))
            return        
        
        nodecnt = 0
        colorgroup = dict()
        adj = dict()
        for n in self.UG.nodes():
            colorname = ('n', self.UG.nodes[n]['routing'], self.UG.nodes[n]['numServer'])
            if colorname not in colorgroup.keys():
                colorgroup[colorname] = set()
            colorgroup[colorname].add(n)
            nodecnt +=1

        augmap = dict() #edge-to-augvertex map
        raugmap = dict() #augvertex-to-edge map            
        for e in self.UG.edges():
            i, j = e
            colorname = ('c', self.UG.edges[e]['capacity'])
            if colorname not in colorgroup.keys():
                colorgroup[colorname] = set()
            augnode = nodecnt
            nodecnt += 1      
            colorgroup[colorname].add(augnode)
            augmap[e] = augnode
            raugmap[augnode] = e

            if i not in adj.keys():
                adj[i] = list()
            if j not in adj.keys():
                adj[j] = list()
            if augnode not in adj.keys():
                adj[augnode] = list()
            adj[i].append(augnode)
            adj[augnode].append(i)
            adj[j].append(augnode)
            adj[augnode].append(j)

        g = pynauty.Graph(nodecnt, adjacency_dict=adj, vertex_coloring=list(colorgroup.values()))
        (gens, _, _, _, _) = pynauty.autgrp(g)

        self.Autgen = set([tuple(g[0:self.UG.number_of_nodes()]) for g in gens])

        stagedata = (self.Autgen)
        pickle.dump(stagedata, open(stagepath, 'wb'))

        
    def findRepresentativeCommodities(self):
        stagepath = HCONST['stagepath'] + '/' + 'findRepresentativeCommodities'
        if os.path.exists(stagepath):
            (self.RepCommodities) = pickle.load(open(stagepath, 'rb'))
            return
        
        tovisit = set()        
        visited = set()
        repcomms = set()

        commodities = list(self.Commodities)
        commodities.sort()
        for repsd in commodities:
            if repsd in visited:
                continue
            repcomms.add(repsd)
            autcomms = set()
            self.saveCommodityAutomorphicMap(repsd, repsd, None)
            tovisit.add((repsd, repsd))
            while len(tovisit) > 0:
                sd, parent = tovisit.pop()
                autcomms.add(sd)
                visited.add(sd)
                for autmap in self.Autgen:
                    asd = applyGenerator(sd, autmap)
                    if asd in visited:
                        continue
                    self.saveCommodityAutomorphicMap(asd, sd, autmap)
                    tovisit.add((asd, sd))

            self.saveCommodityGroup(repsd, autcomms)
        self.RepCommodities = repcomms

        stagedata = (self.RepCommodities)
        pickle.dump(stagedata, open(stagepath, 'wb'))
        

    def saveCommodityGroup(self, repsd, autcomms):
        fpath = HCONST['commpath'] + '/' + '{0}_{1}_CommodityGroup'.format(*repsd)
        pickle.dump(autcomms, open(fpath, 'wb'))

        
    def loadCommodityGroup(self, repsd):
        fpath = HCONST['commpath'] + '/' + '{0}_{1}_CommodityGroup'.format(*repsd)
        return pickle.load(open(fpath, 'rb'))


    def saveCommodityAutomorphicMap(self, sd, parent, autmap):        
        fpath = HCONST['commpath'] + '/' + '{0}_{1}_AutomorphicMap'.format(*sd)
        if sd == parent:
            fmap = tuple(range(self.UG.number_of_nodes()))
            pickle.dump(fmap, open(fpath + '_Forward', 'wb'))
            pickle.dump(fmap, open(fpath + '_Reverse', 'wb'))
        else:
            ppath = HCONST['commpath'] + '/' + '{0}_{1}_AutomorphicMap'.format(*parent)
            pmapfwd = pickle.load(open(ppath + '_Forward', 'rb'))
            fmap = applyGenerator(pmapfwd, autmap)
            rmap = [None]*len(fmap)
            for i in range(len(fmap)):
                rmap[fmap[i]] = i
            rmap = tuple(rmap)
            pickle.dump(fmap, open(fpath + '_Forward', 'wb'))
            pickle.dump(rmap, open(fpath + '_Reverse', 'wb'))


    def loadCommodityAutomorphicMap(self, sd, isForward=True):
        fpath = HCONST['commpath'] + '/' + '{0}_{1}_AutomorphicMap'.format(*sd)
        if isForward:
            return pickle.load(open(fpath + '_Forward', 'rb'))
        else:
            return pickle.load(open(fpath + '_Reverse', 'rb'))


    def findRepresentativeCommodityFlowLinks(self):
        stagepath = HCONST['stagepath'] + '/' + 'findRepresentativeCommodityFlowLinks'
        if os.path.exists(stagepath):
            (self.RepCommFlowLinks) = pickle.load(open(stagepath, 'rb'))
            return

        self.RepCommFlowLinks = dict()
        pool = mp.Pool(self.NumThread)
        for repsd, repflowlinks in pool.imap_unordered(self.findRepresentativeCommodityFlowLinksByCommodity, self.RepCommodities):
            self.RepCommFlowLinks[repsd] = repflowlinks
        pool.close()
        pool.join()

        stagedata = (self.RepCommFlowLinks)
        pickle.dump(stagedata, open(stagepath, 'wb'))
    

    def findRepresentativeCommodityFlowLinksByCommodity(self, repsd):
        autgen = set()
        for autmap in self.Autgen:
            if involve(repsd[0], autmap) or involve(repsd[1], autmap):
                continue
            autgen.add(autmap)

        tovisit = set()
        visited = set()
        repflowlinks = set()
        flowlinkmap = dict() # flowlink-to-representative mapping

        links = list(self.DLinks)
        links.sort()
        for canlink in links:
            if canlink in visited:
                continue
            repflowlinks.add(canlink)
            flowlinkmap[canlink] = canlink
            tovisit.add(canlink)
            while len(tovisit) > 0:
                link = tovisit.pop()
                visited.add(link)
                for autmap in autgen:
                    alink = applyGenerator(link, autmap)
                    if alink in visited:
                        continue
                    flowlinkmap[alink] = flowlinkmap[link]
                    tovisit.add(alink)
        self.saveCommodityFlowLinkMap(repsd, flowlinkmap)
        return (repsd, repflowlinks)


    def saveCommodityFlowLinkMap(self, repsd, flowlinkmap):
        fpath = HCONST['flowpath'] + '/' + '{0}_{1}_FlowLinkMap'.format(*repsd)
        pickle.dump(flowlinkmap, open(fpath, 'wb'))


    def loadCommodityFlowLinkMap(self, repsd):
        fpath = HCONST['flowpath'] + '/' + '{0}_{1}_FlowLinkMap'.format(*repsd)
        return pickle.load(open(fpath, 'rb'))


    def findRepresentativeAuxs(self):
        stagepath = HCONST['stagepath'] + '/' + 'findRepresentativeAuxs'
        if os.path.exists(stagepath):
            (self.RepAuxiliarys) = pickle.load(open(stagepath, 'rb'))
            return
        
        auxindice = [(u, i, j) for u in self.HostNodes for (i, j) in self.DLinks]
        auxindice.sort()

        tovisit = set()        
        visited = set()
        repauxs = set()

        for repaux in auxindice:
            if repaux in visited:
                continue
            repauxs.add(repaux)
            autauxs = set()
            tovisit.add(repaux)
            while len(tovisit) > 0:
                aux = tovisit.pop()
                autauxs.add(aux)
                visited.add(aux)
                for autmap in self.Autgen:
                    aaux = applyGenerator(aux, autmap)
                    if aaux in visited:
                        continue
                    tovisit.add(aaux)

            self.saveAuxiliaryGroup(repaux, autauxs)
        self.RepAuxiliarys = repauxs

        stagedata = (self.RepAuxiliarys)
        pickle.dump(stagedata, open(stagepath, 'wb'))                


    def findRepresentativeAuxsParallel(self):
        stagepath = HCONST['stagepath'] + '/' + 'findRepresentativeAuxs'
        if os.path.exists(stagepath):
            (self.RepAuxiliarys) = pickle.load(open(stagepath, 'rb'))
            return
        
        auxindice = [(u, i, j) for u in self.HostNodes for (i, j) in self.DLinks]
        auxindice.sort()

        tovisit = set()        
        visited = set()
        repauxs = set()

        for repaux in auxindice:
            if repaux in visited:
                continue
            repauxs.add(repaux)
            autauxs = set()
            tovisit.add(repaux)
            pool = mp.Pool(self.NumThread)
            while len(tovisit) > 0:
                autauxs.update(tovisit)
                visited.update(tovisit)                
                currnodes = tuple(tovisit)
                tovisit.clear()
                for nextnodes in pool.imap_unordered(self.findNextLevelAuxs, currnodes):
                    tovisit.update(nextnodes.difference(visited))
            self.saveAuxiliaryGroup(repaux, autauxs)
            pool.close()
            pool.join()
        self.RepAuxiliarys = repauxs

        stagedata = (self.RepAuxiliarys)
        pickle.dump(stagedata, open(stagepath, 'wb'))                
                

    def findNextLevelAuxs(self, aux):
        nextnodes = set()
        for autmap in self.Autgen:
            aaux = applyGenerator(aux, autmap)
            nextnodes.add(aaux)
        return nextnodes

        
    def saveAuxiliaryGroup(self, repaux, autauxs):
        fpath = HCONST['auxpath'] + '/' + '{0}_{1}_{2}_AuxiliaryGroup'.format(*repaux)
        pickle.dump(autauxs, open(fpath, 'wb'))

        
    def loadAuxiliaryGroup(self, repaux):
        fpath = HCONST['auxpath'] + '/' + '{0}_{1}_{2}_AuxiliaryGroup'.format(*repaux)
        return pickle.load(open(fpath, 'rb'))


    def computeAuxReverseMap(self):
        for u in self.HostNodes:
            auxtorep = dict()
            for repaux in self.RepAuxiliarys:
                autauxs = self.loadAuxiliaryGroup(repaux)
                for (n, i, j) in autauxs:
                    if n != u:
                        continue
                    auxtorep[i, j] = repaux
            fpath = HCONST['auxpath'] + '/' + '{0}_AuxToRep'.format(u)
            pickle.dump(auxtorep, open(fpath, 'wb'))

            
    def loadAuxToRep(self, node):
        fpath = HCONST['auxpath'] + '/' + '{0}_AuxToRep'.format(node)
        return pickle.load(open(fpath, 'rb'))
        

    def findRepresentativeLinkConstrs(self):
        stagepath = HCONST['stagepath'] + '/' + 'findRepresentativeLinkConstrs'
        if os.path.exists(stagepath):
            (self.RepLinkConstrs) = pickle.load(open(stagepath, 'rb'))
            return

        repgroups = dict()
        pool = mp.Pool(self.NumThread)
        for (link, encode) in pool.imap_unordered(self.encodeLinkConstraint, self.DLinks):
            if encode not in repgroups:
                repgroups[encode] = set()
            repgroups[encode].add(link)
        pool.close()
        pool.join()

        replinks = set()
        for links in repgroups.values():
            replinks.add(links.pop())

        self.RepLinkConstrs = replinks

        stagedata = (self.RepLinkConstrs)
        pickle.dump(stagedata, open(stagepath, 'wb'))        

        
    def encodeLinkConstraint(self, link):
        count = dict()
        for auxidx in self.RepAuxiliarys:
            count['b', auxidx] = 0
            count['g', auxidx] = 0

        for u in self.HostNodes:
            auxtorep = self.loadAuxToRep(u)
            auxidx = auxtorep[link]
            count['b', auxidx] += 1
            count['g', auxidx] += 1

        encode = tuple(count.values())
        return link, encode

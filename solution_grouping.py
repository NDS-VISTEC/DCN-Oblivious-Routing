# Copyright (c) 2023 VISTEC - Vidyasirimedhi Institute of Science and Technology
# Distribute under MIT License
# Authors:
#  - Sucha Supittayapornpong <sucha.s[-at-]vistec.ac.th>
#  - Kanatip Chitavisutthivong <kanatip.c_s18[-at-]vistec.ac.th>

import os
import pickle
import multiprocessing as mp

import state_helper as helper
from state_helper import HCONST
from topology_automorphism import applyGenerator

from state_helper import HCONST, initHCONST
import math
import gc

class SolutionGrouping:
    """
    SolutionGrouping class 

    ...

    Attributes
    ----------
    rootdir : str
        root directory path
    toponame : str
        topology name
    numThread : int
        a number of threads
    Topo : Topology
        Topology object
    Route : dict
        Route
    remainedNodes : list
        a list of unfinished nodes
    selectedNodes : list
        a list of nodes 
    """
    def __init__(self, rootdir, toponame, numThread=1):
        self.rootdir = rootdir
        self.toponame = toponame
        self.numThread = numThread

        helper.initHCONST(self.rootdir, self.toponame)
        helper.makeSplitGroupsDirectory()

        print('-------------------------')
        print('Step: Solution Grouping')
        print('-------------------------')

        if not os.path.exists(HCONST['outputpath'] + '/' + 'OptimalRouting') or not os.path.exists(HCONST['outputpath'] + '/' + 'Topology'):
            print("\t Optimal solution does not exist")
            return

        self.Topo = pickle.load(open(HCONST['outputpath'] + '/' + 'Topology', 'rb'))
        self.Route = pickle.load(open(HCONST['outputpath'] + '/' + 'OptimalRouting', 'rb'))
        allnodes = list(self.Topo.AllNodes)
        
        if not os.path.exists(HCONST['outputpath'] + '/' + 'SelectedNodes'):
            self.selectedNodes = allnodes
            pickle.dump(self.selectedNodes, open(HCONST['outputpath'] + '/' + 'SelectedNodes', 'wb'))
        else:
            self.selectedNodes = pickle.load(open(HCONST['outputpath'] + '/' + 'SelectedNodes', 'rb'))

        if not os.path.exists(HCONST['outputpath'] + '/' + 'RemainedNodes'):
            self.remainedNodes = self.selectedNodes
        else:
            self.remainedNodes = pickle.load(open(HCONST['outputpath'] + '/' + 'RemainedNodes', 'rb'))

    def groupSolution(self):
        
        allnodes = self.remainedNodes.copy()
        pool = mp.Pool(self.numThread)
        for node in pool.imap_unordered(self.groupSolutionAtNode, allnodes):
            self.remainedNodes.remove(node) 
            pickle.dump(self.remainedNodes, open(HCONST['outputpath'] + '/' + 'RemainedNodes', 'wb'))
        pool.close()
        pool.join()

        if len(self.remainedNodes) == 0:
            print('\t Complete')
            self.getStatCountInfo()
            return 


    def countRouteInfoAtNode(self, splitgroups, node):
        Topo = self.Topo
        cntall = 0
        cntcpt = 0
        count = dict()

        for repsd in Topo.RepCommodities:
            for sdgrp in splitgroups[repsd].keys():
                if len(sdgrp) == 0:
                    continue
                cntall += len(splitgroups[repsd][sdgrp])
                cntcpt += 1
        count['all'] = cntall
        count['compact'] = cntcpt
        pickle.dump(count, open(HCONST['splitgroupspath'] + '/' + 'CountRouteInfo_'+ str(node), 'wb'))

        return cntall, cntcpt


    def groupSolutionAtNode(self, node):
        splitgroups = dict()
        for repsd in self.Topo.RepCommodities:
            commsplit = dict()
            autcomms = self.Topo.loadCommodityGroup(repsd)
            for autsd in autcomms:
                code = self.encodeFlows(node, repsd, autsd)
                if code not in commsplit:
                    commsplit[code] = set()
                commsplit[code].add(autsd)
            splitgroups[repsd] = commsplit
        pickle.dump(splitgroups, open(HCONST['splitgroupspath'] + '/' + 'SplitGroupsAtNodes_'+ str(node), 'wb'))
        self.countRouteInfoAtNode(splitgroups, node)
        del splitgroups
        gc.collect()
        return node


    def encodeFlows(self, node, repsd, sd):
        flowlinkmap = self.Topo.loadCommodityFlowLinkMap(repsd)
        code = list()        
        for nh in self.Topo.UG.neighbors(node):
            link = (node, nh)
            rmap = self.Topo.loadCommodityAutomorphicMap(sd, isForward=False)
            alink = applyGenerator(link, rmap)
            repflowlink = flowlinkmap[alink]
            if repsd in self.Route.get_edge_data(*repflowlink).keys():
                code.append((link, repflowlink, self.Route.get_edge_data(*repflowlink)[repsd]))
        code.sort()
        return tuple(code)


    def getCountInfoAtNode(self, node):
        count = pickle.load(open(HCONST['splitgroupspath'] + '/' + 'CountRouteInfo_'+ str(node), 'rb'))
        return (count['all'], count['compact'])
    

    def getStatCountInfo(self):
        Topo = self.Topo

        allnodes = list(Topo.AllNodes)
        ratio = [self.getCountInfoAtNode(node)[1]/self.getCountInfoAtNode(node)[0] for node in allnodes]
        print('\t Min reduction: ', min(ratio))
        print('\t Max reduction: ', max(ratio))
        print('\t Average reduction: ', sum(ratio)/float(len(ratio)))

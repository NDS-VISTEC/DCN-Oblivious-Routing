# Copyright (c) 2023 VISTEC - Vidyasirimedhi Institute of Science and Technology
# Distribute under MIT License
# Authors:
#  - Sucha Supittayapornpong <sucha.s[-at-]vistec.ac.th>
#  - Kanatip Chitavisutthivong <kanatip.c_s18[-at-]vistec.ac.th>

import time
import pickle
import networkx as nx
import gurobipy as gp
import os
import itertools

import state_helper as helper
from state_helper import HCONST


DEFAULT_MAX_TIMEOUT = 12 * 60 * 60 # 12 hours

class Optimization:
    """
    Class Optimization

    ...

    Attributes
    ----------
    Name : str
        a class name
    NumLPThread : int
        a number of thread
    MaxTimeout : bool
        solver maximum time out
    Topo : Topology
        Topology object
    M : gurobipy.Model
        optimization model
    R : gurobipy.Variable
        throughput variable
    F : dict
        flow variables
    B : dict
        source auxiliary
    G : dict
        destination auxiliary

    """

    def __init__(self, topology, numLPThread=1, maxTimeout=DEFAULT_MAX_TIMEOUT):
        self.Name = 'Optimization-' + topology.Name
        self.NumLPThread = numLPThread
        self.MaxTimeout = maxTimeout
        
        self.Topo = topology
        self.M = None  # Optimization model
        self.R = None  # Throughput variable
        self.F = None  # Flow variables
        self.B = None  # Source auxiliary
        self.G = None  # Destination auxiliary

        parameters = (self.Name, self.NumLPThread)
        pickle.dump(parameters, open(HCONST['outputpath'] + '/' + 'Parameters', 'wb'))
        pickle.dump(self.Topo, open(HCONST['outputpath'] + '/' + 'Topology', 'wb'))

        print('-------------------------')
        print('Step: Optimization')
        print('-------------------------')


    def optimize(self):
        if os.path.exists(HCONST['outputpath'] + '/' + 'ComputedThroughput'):
            print("\t Existing optimal solution is available.")
            return
        
        overallOptTime = time.time()
        iterationTimes = dict()
        
        self.initialModel()
        self.createVariables()
        self.setObjective()
        self.setFlowConservationConstraint()
        self.setAdditionalFlowConstraint()
        self.setAuxThroughputConstraint()
        self.setAuxFlowConstraint()

        opttime = time.time()
        throughput = self.computeOptimalSolution()
        opttime = time.time() - opttime

        if throughput != None:
            print('\t Throughput = {0:.5}, Opttime = {1:.2f}'.format(throughput, opttime))
            pickle.dump(throughput, open(HCONST['outputpath'] + '/' + 'ComputedThroughput', 'wb'))
            pickle.dump(opttime, open(HCONST['outputpath'] + '/' + 'OptimizationTime', 'wb'))
            self.saveOptimalRouting()


    def initialModel(self):
        M = gp.Model(name=self.Name)
        M.setParam('OutputFlag', 0)
        M.setParam('Threads', self.NumLPThread)
        M.setParam('Method', -1)
        M.setParam('TimeLimit', self.MaxTimeout)
        self.M = M
        

    def createVariables(self):
        M = self.M
        Topo = self.Topo

        R = M.addVar(lb=0, vtype=gp.GRB.CONTINUOUS, name='r')
        self.R = R

        F = dict()
        for repsd in Topo.RepCommodities:
            F[repsd] = dict()
            for repflowlink in Topo.RepCommFlowLinks[repsd]:
                linkcap = Topo.UG.get_edge_data(*repflowlink)['capacity']
                F[repsd][repflowlink] = M.addVar(lb=0, ub=linkcap,
                                                 vtype=gp.GRB.CONTINUOUS,
                                                 name='f_{0}_{1}_{2}_{3}'.format(repsd[0], repsd[1],
                                                                                 repflowlink[0], repflowlink[1]))
        self.F = F

        B = dict() # beta
        for repaux in Topo.RepAuxiliarys:
            B[repaux] = M.addVar(lb=0, vtype=gp.GRB.CONTINUOUS, name='b_{0}_{1}_{2}'.format(*repaux))
        self.B = B

        G = dict() # gamma
        for repaux in Topo.RepAuxiliarys:
            G[repaux] = M.addVar(lb=0, vtype=gp.GRB.CONTINUOUS, name='g_{0}_{1}_{2}'.format(*repaux))
        self.G = G
                                 

    def setObjective(self):
        Topo = self.Topo        
        M = self.M
        R = self.R

        M.setObjective(R, sense=gp.GRB.MINIMIZE)


    def setFlowConservationConstraint(self):
        Topo = self.Topo        
        M = self.M
        F = self.F

        for repsd in Topo.RepCommodities:
            s, d = repsd
            flowmap = Topo.loadCommodityFlowLinkMap(repsd)
            nodes = Topo.AllNodes
            for n in nodes:
                flowin = sum(F[repsd][flowmap[h, n]] for h in Topo.UG.neighbors(n)) + (1 if n == s else 0)
                flowout = sum(F[repsd][flowmap[n, h]] for h in Topo.UG.neighbors(n)) + (1 if n == d else 0)
                M.addConstr(flowin == flowout, name='fc_{0}_{1}_{2}'.format(s, d, n))

                
    def setAdditionalFlowConstraint(self):
        Topo = self.Topo        
        M = self.M
        F = self.F

        # No flows to routing non-capable nodes
        for repsd in Topo.RepCommodities:
            s, d = repsd
            avoidlinks = itertools.product(Topo.AllNodes, Topo.NonRouteNodes.difference([d]))
            for i, j in Topo.RepCommFlowLinks[repsd].intersection(avoidlinks):
                M.addConstr(F[repsd][i, j] == 0, name='afa_{0}_{1}_{2}_{3}'.format(s, d, i, j))

        # No flows route back to source and route away from destination
        for repsd in Topo.RepCommodities:
            s, d = repsd
            for i, j in Topo.RepCommFlowLinks[repsd]:
                if j == s or i == d:
                    M.addConstr(F[repsd][i, j] == 0, name='afc_{0}_{1}_{2}_{3}'.format(s, d, i, j))


    def setAuxThroughputConstraint(self):
        Topo = self.Topo
        M = self.M
        B = self.B
        G = self.G
        R = self.R

        for i, j in Topo.RepLinkConstrs:
            lhs = 0
            for u in Topo.HostNodes:
                linkauxtorep = Topo.loadAuxToRep(u)
                auxidx = linkauxtorep[i, j]
                lhs += Topo.UG.nodes[u]['numServer'] * (B[auxidx] + G[auxidx])
            M.addConstr(lhs <= R, name='auxtc_{0}_{1}'.format(i, j))


    def setAuxFlowConstraint(self):
        Topo = self.Topo
        M = self.M
        F = self.F
        B = self.B
        G = self.G        

        for repsd in Topo.RepCommodities:
            for repflowlink in Topo.RepCommFlowLinks[repsd]:
                linkcap = Topo.UG.get_edge_data(*repflowlink)['capacity']
                srclinkauxtorep = Topo.loadAuxToRep(repsd[0])
                bauxidx = srclinkauxtorep[repflowlink]
                dstlinkauxtorep = Topo.loadAuxToRep(repsd[1])
                gauxidx = dstlinkauxtorep[repflowlink]
                lhs = F[repsd][repflowlink]/linkcap - B[bauxidx] - G[gauxidx]
                M.addConstr(lhs <= 0, name='auxfc_{0}_{1}_{2}_{3}'.format(*repsd, *repflowlink))

                
    def computeOptimalSolution(self):
        M = self.M
        M.optimize()

        if M.status == gp.GRB.OPTIMAL:
            throughput = 1.0/M.ObjVal
            return throughput
        elif M.status == gp.GRB.TIME_LIMIT:
            self.saveIntermediateRouting()
            return None
        else:
            print('****', M.status)
            assert False, 'Main optimization fails'

            
    def saveOptimalRouting(self):
        Topo = self.Topo
        F = self.F

        g = nx.DiGraph()
        for node in Topo.UG.nodes():
            g.add_node(node)
        for i, j in Topo.UG.edges():
            g.add_edge(i, j)
            g.add_edge(j, i)
            for repsd in Topo.RepCommodities:
                flowmap = Topo.loadCommodityFlowLinkMap(repsd)
                flowij = F[repsd][flowmap[i, j]].X
                flowji = F[repsd][flowmap[j, i]].X                    

                if flowij > 0:
                    g[i][j][repsd] = flowij

                if flowji > 0:
                    g[j][i][repsd] = flowji

        pickle.dump(g, open(HCONST['outputpath'] + '/' + 'OptimalRouting', 'wb'))


    def saveIntermediateRouting(self):
        Topo = self.Topo
        F = self.F

        g = nx.DiGraph()
        for node in Topo.UG.nodes():
            g.add_node(node)
        for i, j in Topo.UG.edges():
            g.add_edge(i, j)
            g.add_edge(j, i)
            for repsd in Topo.RepCommodities:
                flowmap = Topo.loadCommodityFlowLinkMap(repsd)
                flowij = F[repsd][flowmap[i, j]].X
                flowji = F[repsd][flowmap[j, i]].X                    

                if flowij > 0:
                    g[i][j][repsd] = flowij

                if flowji > 0:
                    g[j][i][repsd] = flowji
        
        pickle.dump(g, open(HCONST['outputpath'] + '/' + 'IntermediateRouting', 'wb'))

        intermediatesolution = {v.varName: v.X for v in M.getVars()}
        pickle.dump(intermediatesolution, open(HCONST['outputpath'] + '/' + 'IntermediateSolution', 'wb'))

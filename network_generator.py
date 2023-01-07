# Copyright (c) 2023 VISTEC - Vidyasirimedhi Institute of Science and Technology
# Distribute under MIT License
# Authors:
#  - Sucha Supittayapornpong <sucha.s[-at-]vistec.ac.th>
#  - Kanatip Chitavisutthivong <kanatip.c_s18[-at-]vistec.ac.th>

import networkx as nx
import itertools
import numpy as np


def generateFatClique(parameters):
    """ Generate FatClique Topology

        M. Zhang, R. N. Mysore, S. Supittayapornpong, and R. Govindan, “Understanding lifecycle management complexity of datacenter topologies,”
        in 16th USENIX Symposium on Networked Systems Design and Implementation (NSDI 19). Boston, MA: USENIX Association, Feb. 2019, pp. 235-254.

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numLocalToR : int
            the number of ToRs in a sub-block
        numSubblock : int
            the number of sub-blocks in a block
        numBlock : int
            the number of blocks
    """
    numServerPerToR = parameters['numServerPerToR']
    numLocalToR = parameters['numLocalToR']
    numSubblock = parameters['numSubblock']
    numBlock = parameters['numBlock']
    name = 'FatClique-{0}-{1}-{2}-{3}'.format(numServerPerToR, numLocalToR, numSubblock, numBlock)
    G0 = nx.Graph()

    for bl in range(numBlock):
        for sb in range(numSubblock):
            for tr in range(numLocalToR):
                G0.add_node(tr + numLocalToR*sb + (numLocalToR*numSubblock)*bl,
                            type='tor',
                            numServer=numServerPerToR,
                            routing=True,
                            tor=tr,
                            subblock=sb,
                            block=bl)

    # Add intra local edges
    for bl in range(numBlock):
        for sb in range(numSubblock):
            nodes = [(numLocalToR*numSubblock)*bl + (numLocalToR)*sb + tr for tr in range(numLocalToR)]
            for (i, j) in itertools.combinations(nodes, 2):
                G0.add_edge(i, j, capacity=1)

    # Add subblock edges
    for bl in range(numBlock):
        for tr in range(numLocalToR):
            nodes = [(numLocalToR*numSubblock)*bl + (numLocalToR)*sb + tr for sb in range(numSubblock)]
            for (i, j) in itertools.combinations(nodes, 2):
                G0.add_edge(i, j, capacity=1)

    # Add block edges
    for sb in range(numSubblock):
        for tr in range(numLocalToR):
            nodes = [(numLocalToR*numSubblock)*bl + (numLocalToR)*sb + tr for bl in range(numBlock)]
            for (i, j) in itertools.combinations(nodes, 2):
                G0.add_edge(i, j, capacity=1)

    return G0, name


def generate2LevelClos(parameters):
    """ Generate a example of Two-level Clos Topology

        Parameters
        ----------
        numServer : int
            the number of server in a lower switch
    """
    numServer = parameters['numServer']
    G0 = nx.Graph()
    lowers = [0, 1, 2, 3]
    uppers = [4, 5]

    for n in lowers:
        G0.add_node(n, type='lower', numServer=numServer, routing=True)
    for n in uppers:
        G0.add_node(n, type='upper', numServer=0, routing=True)
    
    for l in lowers:
        for u in uppers:
            G0.add_edge(l, u, capacity=1)

    name = '2LevelClos-{0}-4-2'.format(numServer)
    return G0, name


def generateFatTreePartial(parameters):
    """ Generate Partially-deployed FatTree Topology

        Parameters
        ----------
        switchRadix : int
            the switch radix
        numAgg : int
            the number of deployed aggregation blocks

    """
    switchRadix = parameters['switchRadix']
    numAgg = parameters['numAgg']
    assert numAgg <= switchRadix
    numServer = int(switchRadix/2)
    numToRPerAgg = int(switchRadix/2)
    numSwitchPerAgg = int(switchRadix/2)
    numUplinkPerAggSwitch = int(switchRadix/2)    
    numSpi = int(numUplinkPerAggSwitch*numSwitchPerAgg*numAgg/switchRadix)

    totToR = numToRPerAgg*numAgg
    
    def torId(tr, agg):
        return tr + numToRPerAgg*agg

    def anodeId(sw, agg):
        return sw + numSwitchPerAgg*agg + totToR

    def snodeId(spi):
        return spi + numSwitchPerAgg*numAgg + totToR

    G0 = nx.Graph()
    
    for agg in range(numAgg):
        for tr in range(numToRPerAgg):
            G0.add_node(torId(tr, agg),
                        numServer=numServer,
                        routing=True,
                        type='tor',
                        tor=tr,
                        agg=agg)
        for sw in range(numSwitchPerAgg):
            G0.add_node(anodeId(sw, agg),
                        numServer=0,
                        routing=True,
                        type='switch',
                        sw=sw,
                        agg=agg)

    for spi in range(numSpi):
        G0.add_node(snodeId(spi),
                    type='switch',
                    numServer=0,
                    routing=True,
                    spi=spi)

    for agg in range(numAgg):
        for sw in range(numSwitchPerAgg):
            for tr in range(numToRPerAgg):
                G0.add_edge(anodeId(sw, agg), torId(tr, agg),
                            capacity=1)

    numrep = int(np.floor(numUplinkPerAggSwitch*numSwitchPerAgg*1.0/numSpi))
    numcommonlink = numrep * numSpi
    residue = numUplinkPerAggSwitch*numSwitchPerAgg % numSpi
    for agg in range(numAgg):
        cnt = 0        
        for sw in range(numSwitchPerAgg):
            for i in range(numUplinkPerAggSwitch):
                cnt += 1
                if cnt <= numcommonlink:
                    spi = (i + sw*numUplinkPerAggSwitch) % numSpi
                else:
                    spi = (i + sw*numUplinkPerAggSwitch + residue*agg) % numSpi
                aid, sid = anodeId(sw, agg), snodeId(spi)
                if not G0.has_edge(aid, sid):
                    G0.add_edge(aid, sid,
                                capacity=1)
                else:
                    G0[aid][sid]['capacity'] += 1    

    for spi in range(numSpi):
        sid = snodeId(spi)
        assert sum(G0[sid][h]['capacity'] for h in G0.neighbors(sid)) == switchRadix

    name = 'FatTree-{0}-{1}'.format(switchRadix, numAgg)
    return G0, name


def generateRing(parameters):
    """ Generate Ring Topology

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numToR : int
            the number of ToRs
        linkCapacity : float
            link capacity for an edge

    """
    numServerPerToR = parameters['numServerPerToR']
    numToR = parameters['numToR']
    linkCapacity = parameters['linkCapacity']
    name = 'Ring-{0}-{1}-{2}'.format(numServerPerToR, numToR, linkCapacity)
    G0 = nx.Graph()

    for tr in range(numToR):
        G0.add_node(tr,
                    type='tor',
                    numServer=numServerPerToR,
                    routing=True,
                    tor=tr)

    for tr in range(numToR):
        if not G0.has_edge(tr, (tr+1) % numToR):
            G0.add_edge(tr, (tr+1) % numToR, capacity=linkCapacity)
        else:
            G0[tr][(tr+1) % numToR]['capacity'] += linkCapacity

    return G0, name


def generateGrid2D(parameters):
    """ Generate Grid2D Topology

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numRow : int
            the number of rows
        numCol : int
            the number of columns
        linkCapacity : float
            link capacity for an edge

    """
    numServerPerToR = parameters['numServerPerToR']
    numRow = parameters['numRow']
    numCol = parameters['numCol']
    linkCapacity = parameters['linkCapacity']
    name = 'Grid2D-{0}-{1}-{2}-{3}'.format(numServerPerToR, numRow, numCol, linkCapacity)
    G0 = nx.Graph()

    def nodeid(r, c):
        return c + r*numCol
    
    for r in range(numRow):
        for c in range(numCol):
            G0.add_node(nodeid(r, c), numServer=numServerPerToR, routing=True, row=r, col=c)


    for r in range(numRow):
        for c in range(numCol-1):
            G0.add_edge(nodeid(r, c), nodeid(r, c+1), capacity=linkCapacity)

    for c in range(numCol):
        for r in range(numRow-1):
            G0.add_edge(nodeid(r, c), nodeid(r+1, c), capacity=linkCapacity)

    return G0, name


def generateTorus2D(parameters):
    """ Generate Torus2D Topology

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numRow : int
            the number of rows
        numCol : int
            the number of columns
        linkCapacity : float
            link capacity for an edge
    """
    numServerPerToR = parameters['numServerPerToR']
    numRow = parameters['numRow']
    numCol = parameters['numCol']
    linkCapacity = parameters['linkCapacity']
    name = 'Torus2D-{0}-{1}-{2}-{3}'.format(numServerPerToR, numRow, numCol, linkCapacity)
    G0 = nx.Graph()

    def nodeid(r, c):
        return c + r*numCol
    
    for r in range(numRow):
        for c in range(numCol):
            G0.add_node(nodeid(r, c), numServer=numServerPerToR, routing=True, row=r, col=c)

    for r in range(numRow):
        for c in range(numCol):
            if not G0.has_edge(nodeid(r, c), nodeid(r, (c+1) % numCol)):
                G0.add_edge(nodeid(r, c), nodeid(r, (c+1) % numCol), capacity=linkCapacity)
            else:
                G0[nodeid(r, c)][nodeid(r, (c+1) % numCol)]['capacity'] += linkCapacity

            if not G0.has_edge(nodeid(r, c), nodeid((r+1) % numRow, c)):
                G0.add_edge(nodeid(r, c), nodeid((r+1) % numRow, c), capacity=linkCapacity)
            else:
                G0[nodeid(r, c)][nodeid((r+1) % numRow, c)]['capacity'] += linkCapacity

    return G0, name


def generateGrid3D(parameters):
    """ Generate Grid3D Topology

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numRow : int
            the number of rows
        numCol : int
            the number of columns
        numLev : int
            the number of levels
        linkCapacity : float
            link capacity for an edge
    """
    numServerPerToR = parameters['numServerPerToR']
    numRow = parameters['numRow']
    numCol = parameters['numCol']
    numLev = parameters['numLev']
    linkCapacity = parameters['linkCapacity']
    name = 'Grid3D-{0}-{1}-{2}-{3}-{4}'.format(numServerPerToR, numRow, numCol, numLev, linkCapacity)
    G0 = nx.Graph()

    def nodeid(r, c, l):
        return c + r*numCol + l*numRow*numCol
    
    for r in range(numRow):
        for c in range(numCol):
            for l in range(numLev):
                G0.add_node(nodeid(r, c, l), numServer=numServerPerToR, routing=True, row=r, col=c, lev=l)

    for r in range(numRow):
        for c in range(numCol):
            for l in range(numLev):
                if r+1 < numRow:
                    G0.add_edge(nodeid(r, c, l), nodeid(r+1, c, l), capacity=linkCapacity)
                if c+1 < numCol:
                    G0.add_edge(nodeid(r, c, l), nodeid(r, c+1, l), capacity=linkCapacity)
                if l+1 < numLev:
                    G0.add_edge(nodeid(r, c, l), nodeid(r, c, l+1), capacity=linkCapacity)

    return G0, name


def generateTorus3D(parameters):
    """ Generate Torus3D Topology

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numRow : int
            the number of rows
        numCol : int
            the number of columns
        numLev : int
            the number of levels
        linkCapacity : float
            link capacity for an edge
    """
    numServerPerToR = parameters['numServerPerToR']
    numRow = parameters['numRow']
    numCol = parameters['numCol']
    numLev = parameters['numLev']
    linkCapacity = parameters['linkCapacity']
    name = 'Torus3D-{0}-{1}-{2}-{3}-{4}'.format(numServerPerToR, numRow, numCol, numLev, linkCapacity)
    G0 = nx.Graph()

    def nodeid(r, c, l):
        return c + r*numCol + l*numRow*numCol
    
    for r in range(numRow):
        for c in range(numCol):
            for l in range(numLev):
                G0.add_node(nodeid(r, c, l), numServer=numServerPerToR, routing=True, row=r, col=c, lev=l)

    for r in range(numRow):
        for c in range(numCol):
            for l in range(numLev):
                if not G0.has_edge(nodeid(r, c, l), nodeid((r+1) % numRow, c, l)):
                    G0.add_edge(nodeid(r, c, l), nodeid((r+1) % numRow, c, l), capacity=linkCapacity)
                else:
                    G0[nodeid(r, c, l)][nodeid((r+1) % numRow, c, l)]['capacity'] += linkCapacity

                if not G0.has_edge(nodeid(r, c, l), nodeid(r, (c+1) % numCol, l)):
                    G0.add_edge(nodeid(r, c, l), nodeid(r, (c+1) % numCol, l), capacity=linkCapacity)
                else:
                    G0[nodeid(r, c, l)][nodeid(r, (c+1) % numCol, l)]['capacity'] += linkCapacity

                if not G0.has_edge(nodeid(r, c, l), nodeid(r, c, (l+1) % numLev)):
                    G0.add_edge(nodeid(r, c, l), nodeid(r, c, (l+1) % numLev), capacity=linkCapacity)
                else:
                    G0[nodeid(r, c, l)][nodeid(r, c, (l+1) % numLev)]['capacity'] += linkCapacity

    return G0, name


def generateDRing(parameters):
    """ Generate DRing Topology

        V. Harsh, S. A. Jyothi, and P. B. Godfrey, “Spineless data centers,” in Proceedings of the 19th ACM Workshop on Hot Topics in Networks, ser. HotNets '20. New York, NY, USA: Association for Computing Machinery, 2020, pp. 67-73.

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numToRPerBlock : int
            the number of ToRs in a block
        numBlock : int
            the number of blocks
        linkCapacity : float
            link capacity for an edge
    """
    numServerPerToR = parameters['numServerPerToR']
    numToRPerBlock = parameters['numToRPerBlock']
    numBlock = parameters['numBlock']
    linkCapacity = parameters['linkCapacity']
    name = 'DRing-{0}-{1}-{2}'.format(numServerPerToR, numToRPerBlock, numBlock, linkCapacity)
    G0 = nx.Graph()
    
    def nodeid(tor, block):
        return tor + numToRPerBlock*block

    for block in range(numBlock):    
        for tor in range(numToRPerBlock):
            inode = nodeid(tor, block)
            G0.add_node(inode,
                        type='tor',
                        numServer=numServerPerToR,
                        routing=True,
                        tor=tor,
                        block=block)

    for block in range(numBlock):
        for itor in range(numToRPerBlock):
            inode = nodeid(itor, block)
            for jtor in range(numToRPerBlock):
                jnode = nodeid(jtor, (block+1) % numBlock)
                knode = nodeid(jtor, (block+2) % numBlock)
                G0.add_edge(inode, jnode, capacity=linkCapacity)
                G0.add_edge(inode, knode, capacity=linkCapacity)

    return G0, name


def generateAbstractAugmentExpander(parameters):
    """ Generate AbstractAugmentExpander Topology

        Parameters
        ----------
        groups : dict
            key = groupID, value = dict['numToR' and 'numServerPerToR']
        linkCapInt : dict
            key = groupID, value = link capacity inside the group
        linkCapEx : dict
            key = (g1, g2), value = link capacity from tor in g1 to intermediate switch adjacent to g2
    """
    groups = parameters['groups']
    linkCapInt = parameters['linkCapInt']
    linkCapEx = parameters['linkCapEx']
    G0 = nx.Graph()
    name = 'AbstractAugExpander-{0}'.format(len(groups))

    def nodeid(tor, gid):
        offset = 0
        for k in range(gid):
            offset += groups[k]['numToR']
        return tor + offset

    for gid in groups.keys():
        numToR = groups[gid]['numToR']
        numServerPerToR = groups[gid]['numServerPerToR']
        name += '_{0}_{1}'.format(numToR, numServerPerToR)
        for tor in range(numToR):
            nid = nodeid(tor, gid)
            G0.add_node(nid, numServer = numServerPerToR, routing=True, type='tor',
                        tor=tor, group=gid)

    nodepairid = dict()
    cntnode = G0.number_of_nodes()
    for g1, g2 in itertools.combinations(groups.keys(), 2):
        nid = nodepairid[g1, g2] = nodepairid[g2, g1] = cntnode
        G0.add_node(nid, numServer = 0, routing=True, type='switch', pair=(g1, g2))
        cntnode += 1

    name += '-{0}'.format(len(groups))
    for gid in groups.keys():
        linkcap = linkCapInt[gid]
        name += '_{0}'.format(linkcap)        
        if linkcap == 0:
            continue
        nodes = [n for n in G0.nodes() if G0.nodes[n]['numServer'] > 0 and G0.nodes[n]['group'] == gid]
        for n, m in itertools.combinations(nodes, 2):
            G0.add_edge(n, m, capacity=linkcap)

    for g1, g2 in linkCapEx.keys():
        linkcap = linkCapEx[g1, g2]
        name += '-{0}_{1}_{2}'.format(g1, g2, linkcap)
        if linkcap == 0:
            continue
        sid = nodepairid[g1, g2]
        g1nodes = [n for n in G0.nodes() if G0.nodes[n]['numServer'] > 0 and G0.nodes[n]['group'] == g1]
        for n in g1nodes:
            G0.add_edge(n, sid, capacity=linkcap)

    return G0, name


def slimflyModel():
    return [5, 7, 11, 17, 19, 25, 29, 35, 43, 47, 55, 79]

def loadSlimFly(parameters):
    """ Generate Slimfly Topology

        M. Besta and T. Hoefler, “Slim fly: A cost effective low-diameter network topology,” in SC '14:
        Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis, 2014, pp. 348-359.

        The topology files can be downloaded via https://spcl.inf.ethz.ch/Research/Scalable_Networking/SlimFly/

        Parameters
        ----------
        netRadix : int
            net radix
        numServerPerToR : int
            the number of server per ToR
    """
    netRadix = parameters['netRadix']
    numServerPerToR = parameters['numServerPerToR']
    sf = open('SlimFly/MMS.' + str(netRadix) + '.adj.txt', 'r')
    numSwitch, numLink = sf.readline().split()
    numSwitch = int(numSwitch)
    numLink = int(numLink)

    G = nx.Graph()
    for s in range(numSwitch):
        G.add_node(s, type='tor', routing=True, numServer=numServerPerToR)

    for s in range(numSwitch):
        nodelist = sf.readline().split()
        for node in nodelist:
            G.add_edge(s, int(node)-1, capacity=1)
    name = 'Slimfly-{0}-{1}'.format(netRadix, numServerPerToR)
    return G, name


def generateBinaryCube(parameters):
    """ Generate BinaryCube Topology

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numDim : int
            the number of dimensions
        linkCapacity : float
            link capacity for an edge
    """
    numServerPerToR = parameters['numServerPerToR']
    numDim = parameters['numDim']
    linkCapacity = parameters['linkCapacity']
    name = 'BinaryCube-{0}-{1}-{2}'.format(numServerPerToR, numDim, linkCapacity)
    G0 = nx.Graph()

    numToR = 2**numDim

    def distance(x, y):
        z = x^y
        d = 0
        while z != 0:
            d += z & 1
            z = z >> 1
        return d
            
    for tr in range(numToR):
        G0.add_node(tr,
                    type='tor',
                    numServer=numServerPerToR,
                    routing=True,
                    tor=tr)

    for xtr in range(numToR):
        for ytr in range(numToR):
            if distance(xtr, ytr) == 1:
                G0.add_edge(xtr, ytr, capacity=linkCapacity)

    return G0, name


def generateClique(parameters):
    """ Generate Clique Topology

        Parameters
        ----------
        numServerPerToR : int
            the number of server per ToR
        numToR : int
            the number of ToRs
        linkCapacity : float
            link capacity for an edge
    """
    numServerPerToR = parameters['numServerPerToR']
    numToR = parameters['numToR']
    linkCapacity = parameters['linkCapacity']
    name = 'Clique-{0}-{1}-{2}'.format(numServerPerToR, numToR, linkCapacity)
    G0 = nx.Graph()

    tors = list(range(numToR))

    for tr in tors:
        G0.add_node(tr,
                    type='tor',
                    numServer=numServerPerToR,
                    routing=True,
                    tor=tr)        
    
    for (xtr, ytr) in itertools.combinations(tors, 2):
        G0.add_edge(xtr, ytr, capacity=linkCapacity)

    return G0, name


def generateMixedNodes(parameters):
    """ Generate Mixed Nodes Topology

        Parameters
        ----------
        numGroup : int
            the number of groups
    """
    numGroup = parameters['numGroup']
    name = 'MixedNodes-{0}'.format(numGroup)
    G0 = nx.Graph()

    nid = 0
    for k in range(numGroup):
        G0.add_node(nid, routing=False, numServer=1)
        G0.add_node(nid+1, routing=True, numServer=1)
        G0.add_node(nid+2, routing=True, numServer=2)

        G0.add_edge(nid, nid+1, capacity=1)
        G0.add_edge(nid, nid+2, capacity=1)
        G0.add_edge(nid+1, nid+2, capacity=1)

        nid += 3        

    totnode = 3 * numGroup
    for k in range(numGroup):
        G0.add_edge(3*k + 1, (3*(k+1) + 1) % totnode, capacity=1)
        G0.add_edge(3*k + 2, (3*(k+1) + 2) % totnode, capacity=2)
        
    return G0, name


def generateBCube(parameters):
    """ Generate BCube Topology

        C. Guo, G. Lu, D. Li, H. Wu, X. Zhang, Y. Shi, C. Tian, Y. Zhang, S. Lu, and G. Lv, 
        “Bcube: A high performance, server-centric network architecture for modular data centers,” in ACM SIGCOMM. 
        Association for Computing Machinery, Inc., August 2009.

        Parameters
        ----------
        K : int
            a parameter of BCube topology
        numPort : int
            a number of ports on a switch
    """
    K = parameters['K']
    numPort = parameters['numPort']
    linkCapacity = 1
    name = 'BCube-{0}-{1}'.format(K, numPort)
    G0 = nx.Graph()

    mappingAddrToBaddr = dict()
    mappingBaddrToAddr = dict()

    def addrToBaddr(addr, numPort):
        length = len(addr)
        summ = 0
        for i in range(length):
            summ += addr[i]*numPort**(length-1-i)
        return summ
    
    def baddrToaddr(baddr, K, numPort):
        addr = [0]*(K+1)
        for i in range(K,-1,-1):
            res = baddr % numPort**i
            addr[K-i] = math.floor(baddr/numPort**i)
            baddr = res
        return tuple(addr)

    servers = list(itertools.product(range(numPort), repeat=K+1))
    for n in servers:
        baddr = addrToBaddr(n, numPort)
        mappingAddrToBaddr[n] = baddr
        mappingBaddrToAddr[baddr] = n 
        G0.add_node(baddr, type='server', numServer=K+1, routing=True, addr=n) # Since 'numServer' represent the node capacity H_n, For evaluation, we set 'numServer' to the number of levels (K+1)
    sk = list(itertools.product(range(numPort), repeat=K))
    level = list(range(K+1))
    switches = list(itertools.product(level, sk))
    sw_baddr = len(servers)
    for n in switches:
        mappingAddrToBaddr[n] = sw_baddr
        mappingBaddrToAddr[sw_baddr] = n 
        G0.add_node(sw_baddr, type='switch', numServer=0, routing=True, addr=n)
        sw_baddr += 1

    for n in switches:
        level, sk = n
        range_p = list(range(numPort))
        for i in range(numPort):
            sk_count = 0 
            server = [0]*(K+1)
            for j in range(K+1):
                if level == K-j:
                    server[j] = i
                else:
                    server[j] = sk[sk_count]
                    sk_count += 1
            server = tuple(server)
            server_baddr = mappingAddrToBaddr[server]
            switch_baddr = mappingAddrToBaddr[n]
            G0.add_edge(switch_baddr, server_baddr, capacity=linkCapacity)

    return G0, name, mappingAddrToBaddr, mappingBaddrToAddr

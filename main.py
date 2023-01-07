# Copyright (c) 2023 VISTEC - Vidyasirimedhi Institute of Science and Technology
# Distribute under MIT License
# Authors:
#  - Sucha Supittayapornpong <sucha.s[-at-]vistec.ac.th>
#  - Kanatip Chitavisutthivong <kanatip.c_s18[-at-]vistec.ac.th>

import os
import multiprocessing as mp
import platform
from functools import partial

import network_generator as netgen
from topology_automorphism import Topology
import state_helper as helper
from state_helper import HCONST, initHCONST
from optimization import Optimization
from verification import Verification
from solution_grouping import SolutionGrouping

from bcube_routing import BCubeRouting
from slimfly_routing import SlimFlyRouting

ProcessorCount = mp.cpu_count()
NumThread = ProcessorCount
NumLPThread = ProcessorCount

if platform.system() == 'Darwin':
    mp.set_start_method("fork")  # Workaround for mac


TOPOLOGY = {'BCube': partial(netgen.generateBCube),
            'MixedNodes': partial(netgen.generateMixedNodes),
            'SlimFly': partial(netgen.loadSlimFly),
            'AbstractAugmentExpander': partial(netgen.generateAbstractAugmentExpander),
            'FatTreePartial': partial(netgen.generateFatTreePartial),
            'Torus2D': partial(netgen.generateTorus2D),
            'FatClique': partial(netgen.generateFatClique),
            '2LevelClos': partial(netgen.generate2LevelClos),
            'Clique': partial(netgen.generateClique),
            'BinaryCube': partial(netgen.generateBinaryCube),
            'DRing': partial(netgen.generateDRing),
            'Torus3D': partial(netgen.generateTorus3D),
            'Grid3D': partial(netgen.generateGrid3D),
            'Grid2D': partial(netgen.generateGrid2D),
            'Ring': partial(netgen.generateRing),
        } 


def process(G, toponame, verify, group_solution):
    rootdir = '.'
    initHCONST(rootdir, toponame)
    helper.makePrecomputationDirectory()
    helper.makeOutputDirectory()
    
    topo = Topology(G, toponame, NumThread)
    opt = Optimization(topo, NumLPThread)
    opt.optimize()

    if verify == True:
        ver = Verification(toponame, NumThread)
        ver.verifyAllLinkLoad()
    if group_solution == True:
        grp = SolutionGrouping(rootdir, toponame, NumThread)
        grp.groupSolution()


def run_example(topology, topo_params, verify=True, group_solution=True):
    if topology in TOPOLOGY.keys():
        if topology == 'BCube':
            G, toponame, mappingAddrToBaddr, mappingBaddrToAddr = TOPOLOGY[topology](topo_params)
        else:
            G, toponame = TOPOLOGY[topology](topo_params)
        process(G, toponame, verify, group_solution)
    else:
        print('There is no specified topology in this example.')


def process_SlimflyVAL(G, toponame, verify):
    rootdir = '.'
    initHCONST(rootdir, toponame)
    helper.makePrecomputationDirectory()
    helper.makeOutputDirectory()
    
    topo = Topology(G, toponame, NumThread)
    sfRouting = SlimFlyRouting(topo, NumThread)
    if verify == True:
        sfRouting.verifyAllLinkLoad(NumThread)


def run_SlimflyVAL(topo_params, verify=True):
    G, toponame = TOPOLOGY['SlimFly'](topo_params)
    process_SlimflyVAL(G, toponame, verify)


def process_BCubePaper(G, toponame, topo_params, mappingAddrToBaddr, mappingBaddrToAddr, verify):
    rootdir = '.'
    initHCONST(rootdir, toponame)
    helper.makePrecomputationDirectory()
    helper.makeOutputDirectory()
    
    topo = Topology(G, toponame, NumThread)
    K = topo_params['K']
    numPort = topo_params['numPort']
    bcRouting = BCubeRouting(K, numPort, mappingAddrToBaddr, mappingBaddrToAddr, topo)
    if verify == True:
        bcRouting.verifyAllLinkLoad(NumThread)


def run_BCubePaper(topo_params, verify=True):
    G, toponame, mappingAddrToBaddr, mappingBaddrToAddr = TOPOLOGY['BCube'](topo_params)
    process_BCubePaper(G, toponame, topo_params, mappingAddrToBaddr, mappingBaddrToAddr, verify)


if __name__ == '__main__':

    topo_params = {'numGroup':4}
    run_example('MixedNodes', topo_params=topo_params)

    # topo_params = {'numServerPerToR':1, 'numToR':4, 'linkCapacity':1}
    # run_example('Clique', topo_params=topo_params, , group_solution=True)

    # topo_params = {'K':1, 'numPort':4}
    # run_example('BCube', topo_params=topo_params, verify=False, group_solution=False)
    # run_BCubePaper(topo_params, verify=True)

    # topo_params = {'netRadix':5, 'numServerPerToR':7}
    # run_example('SlimFly', topo_params=topo_params, verify=False, group_solution=False)
    # run_SlimflyVAL(topo_params, verify=True)

    # topo_params = {'numServerPerToR':2, 'numLocalToR':2, 'numSubblock':2, 'numBlock':2}
    # run_example('FatClique', topo_params=topo_params, verify=False, group_solution=False)
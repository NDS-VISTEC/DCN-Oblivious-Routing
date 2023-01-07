# Copyright (c) 2023 VISTEC - Vidyasirimedhi Institute of Science and Technology
# Distribute under MIT License
# Authors:
#  - Sucha Supittayapornpong <sucha.s[-at-]vistec.ac.th>
#  - Kanatip Chitavisutthivong <kanatip.c_s18[-at-]vistec.ac.th>

import os

HCONST = { 'rootdir' : None,
           'precompute directory': 'Precomputation',
           'commodity data directory': 'commodity',
           'flow data directory': 'flow',
           'auxiliary data directory': 'auxiliary',
           'stage data directory': 'stage',
           'commpath': None,
           'flowpath': None,
           'auxpath': None,
           'stagepath': None,
           'output data directory': 'Output',
           'outputpath': None,
           'split groups directory': 'SplitGroups',
           'splitgroupspath': None,
          }


def makePrecomputationDirectory():
    if HCONST['rootdir'] is None:
        print('rootdir has not been set.')
        assert False
    
    rootdir = HCONST['rootdir']
    if not os.path.exists(rootdir):
        os.mkdir(rootdir)

    if not os.path.exists(rootdir + '/' + HCONST['precompute directory']):
        os.mkdir(rootdir + '/' + HCONST['precompute directory'])

    topopath = HCONST['topopath']
    if not os.path.exists(topopath):
        os.mkdir(topopath)

    commpath = HCONST['commpath']
    if not os.path.exists(commpath):
        os.mkdir(commpath)

    flowpath = HCONST['flowpath']
    if not os.path.exists(flowpath):
        os.mkdir(flowpath)

    auxpath = HCONST['auxpath']
    if not os.path.exists(auxpath):
        os.mkdir(auxpath)

    stagepath = HCONST['stagepath']
    if not os.path.exists(stagepath):
        os.mkdir(stagepath)

    
def makeOutputDirectory():
    if HCONST['rootdir'] is None:
        print('rootdir has not been set. No data is save.')
        assert False

    rootdir = HCONST['rootdir']
    if not os.path.exists(rootdir):
        os.mkdir(rootdir)

    if not os.path.exists(HCONST['rootdir'] + '/' + HCONST['output data directory']):
        os.mkdir(HCONST['rootdir'] + '/' + HCONST['output data directory'])
        
    outputpath = HCONST['outputpath']
    if not os.path.exists(outputpath):
        os.mkdir(outputpath)
    
    
def initHCONST(rootdir, toponame):
    HCONST['rootdir'] = rootdir

    topopath = HCONST['rootdir'] + '/' + HCONST['precompute directory'] + '/' + toponame
    HCONST['topopath'] = topopath
    
    commpath = HCONST['topopath'] + '/' + HCONST['commodity data directory']
    HCONST['commpath'] = commpath

    flowpath = HCONST['topopath'] + '/' + HCONST['flow data directory']
    HCONST['flowpath'] = flowpath

    auxpath = HCONST['topopath'] + '/' + HCONST['auxiliary data directory']
    HCONST['auxpath'] = auxpath

    outputpath = HCONST['rootdir'] + '/' + HCONST['output data directory'] + '/' + toponame
    HCONST['outputpath'] = outputpath

    stagepath = HCONST['topopath'] + '/' + HCONST['stage data directory']
    HCONST['stagepath'] = stagepath

    splitgroupspath = HCONST['rootdir'] + '/' + HCONST['output data directory'] + '/' + toponame + '/' + HCONST['split groups directory']
    HCONST['splitgroupspath'] = splitgroupspath


def makeSplitGroupsDirectory():

    splitgroupspath = HCONST['splitgroupspath']
    if not os.path.exists(splitgroupspath):
        os.mkdir(splitgroupspath)

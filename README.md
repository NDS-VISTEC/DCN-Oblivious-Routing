# DCN Oblivious Routing

Designing Optimal Compact Oblivious Routing for Datacenter Networks in Polynomial Time (INFOCOM 2023) <br>
<img src="https://i.imgur.com/s731ITV.jpg" width="900"><br>
This work proposes a process for designing optimal oblivious routing that is programmed compactly on programmable switches. The process consists of three contributions in tandem. 
1. We first transform a robust optimization problem for designing oblivious routing into a linear program, which is solvable in polynomial time but cannot scale for datacenter topologies. <br>
2. We then prove that the repeated structures in a datacenter topology lead to a structured optimal solution. We
use this insight to formulate a scalable linear program, so an optimal oblivious routing solution is obtained in polynomial time for large-scale topologies. <br>
3. For real-world deployment, the optimal solution is converted into forwarding rules for programmable switches with stringent memory. With this constraint, we utilize the repeated structures in the optimal solution to group the forwarding rules, resulting in compact forwarding rules with a much smaller memory requirement. <br>

##  Example results
Extensive evaluations show our process <br>
1. obtains optimal solutions faster and more scalable than a state-of-the-art technique. <br>
2. reduces the memory requirement by no less than 90% for most considered topologies. <br>

<img src="https://i.imgur.com/Ehi7lRy.jpg" width="600"><br>
This figure shows the optimization times of our scalable linear program and the other state-of-the-art techniques.<br>

The maximum times of the scalable linear program are 0.008 sec. for FatClique, 2.97 min. for SlimFly, and 0.026 sec. for BCube.<br><br>
<img src="https://i.imgur.com/MA0aSh6.jpg" width="600"><br>
This figure shows the efficiency of our forwarding rule grouping approach is measured by the percentage of space saving, which is the proportion of rule reduction to non-grouped rules.<br>

Our grouping method reduces more than 90% of the non-grouped forwarding rules under FatClique with no less than 216 nodes and under BCube with no less than 112 nodes. The space saving for SlimFly highly depends on topology configuration. <br>

## Table of contents
-----
  * [Code Structure](#code-structure)
  * [Installation](#installation)
  * [Run the code](#run-the-code)
  * [Slimfly topology](#slimfly-topology)
  * [Using your own topology](#using-your-own-topology)
  * [Citation](#citation)
------

## Code structure
- ```main.py``` consists of templates and examples 
- ```network_generator.py``` for generating the topology
- ```topology_automorphism.py``` for constructing automorphic topology
- ```optimization.py``` for finding optimal routing solution 
- ```verification.py``` for verifying the routing solution  
- ```solution_grouping.py``` for grouping the routing solution  
- ```bcube_routing.py``` for generating BCube route based on original paper
- ```slimfly_routing.py``` for generating SlimFly VAL route based on original paper
- ```state_helper.py``` miscellaneous helper methods
- ```Dockerfile``` for building the Docker image
- ```requirements.txt``` required python packages for the Docker image 


## Installation
### Prerequisite
This software is tested with the following environment
- Ubuntu 20.04 LTS
- Docker 20.10.17 (build 100c701)

### Download code
```shell
$ git clone https://github.com/NDS-VISTEC/DCN-Oblivious-Routing
```

### Build an Docker image
```shell
$ echo $PWD
/home/NDS/
$ ls $PWD
DCN-Oblivious-Routing  gurobi.lic
$ cd DCN-Oblivious-Routing
$ sudo docker build -t dcn-oblivious-routing .
```

## Run the code
Assume you already have WLS client license file (gurobi.lic) in $PWD/gurobi.lic 
```shell
$ echo $PWD
/home/NDS/
$ ls $PWD
DCN-Oblivious-Routing  gurobi.lic
$ sudo docker run --volume=$PWD/gurobi.lic:/opt/gurobi/gurobi.lic:ro --volume=$PWD/DCN-Oblivious-Routing:/app dcn-oblivious-routing
```

## SlimFly topology
For SlimFly topology, it can be downloaded via https://spcl.inf.ethz.ch/Research/Scalable_Networking/SlimFly/ <br>
(1) Extract ```sf.tar.gz``` file <br>
(2) Copy directory ```sf_sc_2014/graphs/adjacency-list-format``` to this project directory <br>
(3) Rename directory from ```adjacency-list-format``` to ```SlimFly``` <br>

## Using your own topology
You can implement your topology in ```network_generator.py``` and create your workflow based on templates in ```main.py```

## Citation
```
@inproceedings{dcn-oblivious-routing-infocom2023,
    title = "Designing Optimal Compact Oblivious Routing for Datacenter Networks in Polynomial Time",
    author = "Chitavisutthivong, Kanatip  and
      So-In, Chakchai  and
      Supittayapornpong, Sucha",
    booktitle = "IEEE INFOCOM 2023 - IEEE Conference on Computer Communications",
    year = "2023",
}
```
## Visit us
<a href="https://vistec.ist/network"><img src="https://i.imgur.com/NV7ADp2.png" height="40"></a>&nbsp;<a href="https://vistec.ist/"><img src="https://i.imgur.com/jNeJIKB.png" height="40"></a>
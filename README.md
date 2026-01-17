# CorteXForge
This project is a framework designed to automate the generation and execution of radio dataset experiments on the [Slices/CorteXlab](https://www.cortexlab.fr/doku.php?id=start) testbed.
It relies on the [GNU Radio](https://www.gnuradio.org) environment to record labeled transmissions of various signals.

## Overview
This project is organized into two main components:
- Scenario generation: this part produces configuration files describing the experiment setup. It creates: 
  - a `scenario.yaml` file defining which nodes will be used on CorteXlab;
  - an `timeline.csv` file orchestrating the role and sequence of these nodes.
- Experiment execution: this part deploys and executes the generates experiment definitions (`timeline.csv`) directly on the [Slices/CorteXlab](https://www.cortexlab.fr/doku.php?id=start) nodes.

## Usage

### 1. Scenario Generator
:warning: This module is implemented in Python 3.13 !

The scenario generator can be executed locally before  deployment in Slices/CorteXlab. It allows configuration of experimental parameters such as:
- selected nodes to be used
- time of recording (in seconds)

### Example usage
- ```git clone https://github.com/Andreaj42/CorteXForge.git```
- ```cd planner```
- ```python3.13 venv .venv```
- ```source .venv/bin/activate```
- ```pip install -r requirements.txt```
- ```python3.13 main.py --duration 600```

### 2. Forge
:warning: This part must be executed directly on the Slices/CorteXlab testbed !

Each nodes defined before in the previous stage will run a GNU Radio flowgraph according to the configuration.


### Example usage
First, connect to the testbed:
- ```ssh username@gw.cortexlab.fr```

Next, book the testbed with your selected nodes (nodes: 5, 10, and 31 here) for the time of recording (increase the value):
- ```oarsub -l {"network_address in ('mnode5.cortexlab.fr', 'mnode10.cortexlab.fr', 'mnode31.cortexlab.fr')"}/nodes=3,walltime=0:20:00 -r "2025-10-12 21:03:00"```

Now clone the project:
- ```git clone https://github.com/Andreaj42/CorteXForge.git```
- ```cd forge```

And move the previously generated ```scenario``` folder into the `forge` directory, then run:
- ```minus task create forge -f```
- ```minus task submit forge.task```

To monitor your experiment, use: 
- ```minus testbed status```


```scenario.yaml``` .example
```yaml
description: Dataset Generator

duration: 300

nodes:
  node6:
    container:
    - image: ghcr.io/andreaj42/cortexforge:latest        
      command: bash -lc "python3 /cortexlab/homes/andrea_joly/CorteXForge/src/forge/main.py rx"
      
  node10:
    container:
     - image: ghcr.io/andreaj42/cortexforge:latest
       command: bash -lc "python3 /cortexlab/homes/andrea_joly/CorteXForge/src/forge/main.py tx --timeline /cortexlab/homes/andrea_joly/timeline.csv"

  node31:
    container:
     - image: ghcr.io/andreaj42/cortexforge:latest
       command: bash -lc "python3 /cortexlab/homes/andrea_joly/CorteXForge/src/forge/main.py tx --timeline /cortexlab/homes/andrea_joly/timeline.csv"
```

### Docker Images
To simplify deployment and ensure reproductibility, we generated a Docker image.
This image extends the standard CorteXlab toolchain and adds the required dependencies for forge.

## Useful links
- [xp.cortexlab.fr](xp.cortexlab.fr/app)
- [wiki.cortexlab.fr](wiki.cortexlab.fr)

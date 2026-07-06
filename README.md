# CorteXforge
CorteXforge is an end-to-end framework designed to automate the generation and execution of radio dataset experiments on the [SLICES-RI/CorteXlab](https://www.cortexlab.fr/doku.php?id=start) testbed.
It relies on the [GNU Radio](https://www.gnuradio.org) environment to record labeled transmissions of various signals.

## Overview
This project is organized into three main components:
- Scenario generation: this part produces configuration files describing the experiment setup. It creates: 
  - a `scenario.yaml` file defining which nodes will be used on CorteXlab;
  - an `timeline.csv` file orchestrating the role and sequence of these nodes.
- Experiment execution: this part deploys and executes the generates experiment definitions (`timeline.csv`) directly on the [SLICES-RI/CorteXlab](https://www.cortexlab.fr/doku.php?id=start) nodes.
- Dataset API

## Quick start (User Guide) :rocket:

### 1. Scenario Generator
:warning: This module is implemented in Python 3.13 !

The scenario generator can be executed locally before  deployment in Slices/CorteXlab. It allows configuration of experimental parameters such as:
- selected nodes to be used
- time of recording (in seconds)

### Example usage
- ```git clone https://github.com/Andreaj42/CorteXForge.git```
- ```python3.13 -m venv .venv```
- ```. .venv/bin/activate```
- ```pip install -e .[planner]```
- ```cortexforge-planner --nodes-path confis/nodes.yaml --duration 600 --output-path my/path/on/cortexlab```

### 2. Forge (Experiment Execution)
:warning: This part must be executed directly on the Slices/CorteXlab testbed !

Each nodes defined before in the previous stage will run a GNU Radio flowgraph according to the configuration.


### Example usage
First, connect to the testbed:
- ```ssh username@gw.cortexlab.fr```

Next, book the testbed with your selected nodes (nodes: 5, 10, and 31 here) for the time of recording (increase the value):
- ```oarsub -l {"network_address in ('mnode5.cortexlab.fr', 'mnode10.cortexlab.fr', 'mnode31.cortexlab.fr')"}/nodes=3,walltime=0:20:00 -r "2025-10-12 21:03:00"```

To delete a job, use:
- ```oardel job_id```

And move the previously generated ```experiment``` folder into your **Cortexlab** home, then run:
- ```minus task create experiment -f```
- ```minus task submit experiment.task```

To monitor your experiment, use: 
- ```minus testbed status```
- ```minus log -d```


### 3. Pre-generated Datasets

Just want to use a dataset without running your own experiments? Simply download one of the pre-generated datasets produced with CorteXforge.

First, install the dataset API:
- ```pip install cortexforge```

List all available datasets:
- ```cortexforge datasets list```

Download a dataset:
- ```cortexforge datasets download <dataset_name>```

For example:
- ```cortexforge datasets download modfore```

### Docker Images :whale:
To simplify deployment and ensure reproductibility, we generated a Docker image.
This image extends the standard CorteXlab toolchain and adds the required dependencies for forge.

## Useful links :link:
- [xp.cortexlab.fr](xp.cortexlab.fr/app)
- [wiki.cortexlab.fr](wiki.cortexlab.fr)

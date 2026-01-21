# Planner

## Usage

### 1. Scenario Generator
:warning: This module is implemented in Python 3.13 !

The scenario generator can be executed locally before  deployment in Slices/CorteXlab. It allows configuration of experimental parameters such as:
- selected nodes to be used
- time of recording (in seconds)

### Example usage
- ```git clone https://github.com/Andreaj42/CorteXForge.git```
- ```python3.13 -m venv .venv```
- ```source .venv/bin/activate```
- ```pip install -e .```
- ```cortexforge-planner```
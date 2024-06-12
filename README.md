# Caaml_to_ini

This repository can be used to convert a .caaml snowprofile into a .ini file where markers of the layers are defined. This can be used for the .pnt SMP Files to label the data.

The origin code is written by Tamara and Felix, LWD Tirol 2024
It is modified to work for all type of profiles and outputs.

## Overview

-   `data/`: .caaml snowprofiles are stored here. Those are used as input files. When you use another location you can change it in the configs
-   `output/`: Processed data is stored here. In format.ini
-   `configs/`: You can change Path and styles here.

## Setup

This repository runs on Python 3.9 and 3.10. For a quick setup run pip install -e . The required packages can also be installed with pip install -r requirements.txt. If wished, create an environment beforehand (eg: conda create --name=snowdragon python=3.9).

## Usage

...to be added

## Structure

.
├── data
│   └── caaml_profiles
├── output
│   └── ini_files
└── configs

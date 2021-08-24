# Resource Export

Finds all Turbot managed AWS VMs and EBS volumes and Azure VMs, and exports metadata about them to a csv file. 

## Prerequisites

To run the scripts, you must have:

- [Python 3.\*.\*](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installing/)

## Setup

This sections details how to set up an environment in order to run the script.

### Virtual environments activation

We recommend the use of [virtual environment](https://docs.python.org/3/library/venv.html).

To setup a virtual environment:

```shell
python3 -m venv .venv
```

Once created, to activate the environment:

```shell
source .venv/bin/activate
```

### Dependencies

Then install Python library dependencies:

```shell
pip3 install -r requirements.txt
```

### Turbot configuration

Credentials and end point details need to be configure before being able to connect to a Turbot installation. This leverages the credentials in the Turbot CLI configuration file.

#### Turbot CLI 
If you haven't already done so, follow the steps here https://turbot.com/v5/docs/reference/cli/installation to install the Turbot CLI and configure your credentials.


## Executing the script

To run a the Python script:

1. Install and configure the [pre-requisites](#pre-requisites)
1. Using the command line, navigate to the directory for the Python script
1. Create and activate the Python virtual environment
1. Install dependencies
1. Run the Python script using the command line
1. Deactivate the Python virtual environment

### Synopsis

```shell
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 main.py --profile default
```

### Options

#### Details
-p, --profile

> [String] Turbot Profile to be used.

--help

> Lists all the options and their usages.

## Virtual environments deactivation

Once the script has been run, it is advised to deactivate the virtual environment if a virtual environment was used
to install the script dependencies.

This is accomplished by running the command:

```shell
deactivate
```

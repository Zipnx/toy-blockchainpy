# Toy BlockChain

ToyChain, per it's name, is a blockchain meant to be used to toy around and learn more
about the functionalities of blockchain distributed systems. Written in python for ease.
The goal of this project is to enable more people to learn, experiment, and hopefully develop their own projects.

At the final stages, I'd like to implement features such as RingCT, then again, should prob make sure TXs work to begin with

## Getting Started

### Setup

Setup a venv environment, activate it and install the required modules:

```
python3 -m venv ./venv/
source ./venv/bin/activate
pip install -r requirements.py
```

The project's directory might have to be added to your PATH env variable.
This can be done by exporting the value directly or by executing

```
source dev_setup.sh
```

### Samples & Tests

Some samples can be run in the ./samples/ directory

```
python3 samples/test.py
```

The test suite can also be executed by running:

```
python3 run_tests.py
```

### Node

The node is still in it's early days but can be used.

To initialize a new node you can use:

```
python3 node/setup
```

The above script will setup everything in a directory which will hold the node's data.
It is extremely useful, when needing to run more than one node for testing purposes.

Afterwards the node can be run by executing the following, with the path you specified
in the setup

```
python3 node /path/to/node/directory
```

## TODO:
- [ ] Major cleanup and documentation of code 
- [ ] More of the RPC functionality
- [ ] Basic wallet app (todo way later)
- [ ] Unit tests UTXO and TX validation
- [ ] Caching in block storage
- [ ] Better error handling, even more of it
- [ ] Bug: Fix the node sometimes rejecting valid blocks
- [ ] Quick: Make sure a node cannot have itself as a peer
- [ ] Node management
- [ ] Peer pinging, and statuses

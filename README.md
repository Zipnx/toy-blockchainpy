# Toy BlockChain

This is a rework of a similar test chain I made a while ago, which's code is
borderline unreadable (let's be real, this will end up like that again)

Built to be easy to understand how a blockchain
works, in conjunction with PoW and such

## Usage:

Setup a venv environment, activate it and install the required packages:

```
python3 -m venv ./venv/
source ./venv/bin/activate
pip install -r requirements.py
```

For now, run the sample scripts in the ./samples/ directory.

```
python3 samples/test.py
```

You may also have to add the project directory in the PATH env variable.
That can be done temporarily, by exporting manually or by running:

```
source dev_setup.sh
```

You could also add it permanently but imma leave that up to you

Will add more stuff when i got time (TXs & UTXOs, maybe a proper chain)


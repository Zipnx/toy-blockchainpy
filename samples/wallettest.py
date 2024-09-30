
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
from binascii import hexlify
import logging
import os,sys

from coretc.chain import Chain
from coretc.settings import ChainSettings

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coretc import Wallet, UTXO
from coretc.utils.generic import data_hexdigest

logger = logging.getLogger('samplelogger')

def main():
    
    chain = Chain(settings = ChainSettings(debug_dont_save = True))
    wallet = Wallet.generate()

    rew1 = wallet.create_reward_transaction(10)


    

if __name__ == '__main__':
    main()

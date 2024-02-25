
#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
from binascii import hexlify
import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from coretc import Wallet, UTXO

def main():
    
    some_utxo_data = {
        'amount': 0.50,
        'txid': 'A'*32,
        'index': 0,
        'pk': '0'*32
    }
    
    utxo_a = UTXO.from_json(some_utxo_data)

    some_utxo_data['amount'] = 1.5
    utxo_b = UTXO.from_json(some_utxo_data)
    
    if utxo_a is None or utxo_b is None: return

    a = Wallet.generate()

    a.owned_utxos += [utxo_a, utxo_b] 

    x = UTXO(a.get_pk_bytes(), 0.5, 0)

    print(hexlify(x.signature).decode())

    x.sign(a.sk, [])

    print(hexlify(x.signature).decode())

    print(x.unlock_spend([]))



    pass        

    

if __name__ == '__main__':
    main()


#!/usr/bin/env python3

# Add the ../ directory to PATH to be able to use coretc
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

    a = Wallet.generate()

    a.owned_utxos += [utxo_a, utxo_b] 

    print(a.get_address_str())
    print('Balance:', a.balance())

    pass        

    

if __name__ == '__main__':
    main()

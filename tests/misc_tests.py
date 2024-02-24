
import unittest

from coretc.crypto import data_sign, data_verify

from Crypto.PublicKey import ECC

class TestMisc(unittest.TestCase):
    
    def setUp(self):
        self.example_privkey = ECC.generate(curve = 'P-256')
        self.example_pubkey  = self.example_privkey.public_key()

    def test_signing(self):
        
        data = b'Data to be signed'

        signature = data_sign(self.example_privkey, data)

        self.assertFalse(signature is None, 'Unable to sign data with private key')

        if signature is None: return

        self.assertTrue(data_verify(self.example_pubkey, data, signature),
                        "Unable to verify data with correspondign public key")

        

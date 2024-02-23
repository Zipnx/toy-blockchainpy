
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

def data_sign(priv: ECC.EccKey, data: bytes) -> bytes | None:
    '''
    Sign a byte array with an ECDSA private key

    Args:
        priv (ECC.EccKey): Private key to be used
        data (bytes): Bytes that will be signed

    Return:
        bytes: Resulting ecc signature
        None: If the supplied key cant be used for signing

    '''

    signer = DSS.new(priv, mode = 'fips-186-3')
    hasher = SHA256.new(data)
    
    if not signer.can_sign(): return None

    return signer.sign(hasher)

def data_verify(pub: ECC.EccKey, data: bytes, signature: bytes) -> bool:
    '''
    Verify data signature using an ECDSA public key

    Args:
        pub (ECC.EccKey): Public key to be used
        data (bytes): The data of which's signature will be tested
        signature (bytes): The signature of said data

    Return:
        bool: Whether the signature was valid
    '''

    signer = DSS.new(pub, mode = 'fips-186-3')
    hasher = SHA256.new(data)

    try:
        signer.verify(hasher, signature)
        return True
    except BaseException:
        return False

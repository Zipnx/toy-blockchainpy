
from jsonschema import validate, ValidationError

# TODO: Do additional format checking for the hex strings, version format, etc...

#
#  REGEX
#
HASH_HEXLIFY_REGEX = '^(?:0x)?[0-9a-fA-F]{64}+$'
HEXSTRING_REGEX = '^(?:0x)?[0-9a-fA-F]{1,512}+$'


#
#  SCHEMAS
#

UTXO_OUT_JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        
        'owner': {'type': 'string'},
        'amount': {'type': 'number', 'format': 'float'},
        'index': {'type': 'number', 'minimum': 0, 'maximum': 255},
        'pk': {'type': 'string'},
    },
    'required': ['owner', 'amount', 'index', 'pk']
}

UTXO_IN_JSON_SCHEMA = {
    'allOf': [
        UTXO_OUT_JSON_SCHEMA,
        {
            'type': 'object',
            'properties': {
                'unlock-sig': {'type': 'string'},
                'txid': {'type': 'string'}
            }
        }
    ]
}

TX_JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        
        'inputs': {
            'type': 'array',
            'items': UTXO_OUT_JSON_SCHEMA,
            'minItems': 0
        },
        
        'outputs': {
            'type': 'array',
            'items': UTXO_IN_JSON_SCHEMA,
            'minItems': 1
        },

        'nonce': {'type': 'string'},
        'txid': {'type': 'string'}

    },
    'required': ['inputs', 'outputs', 'nonce', 'txid']
}

BLOCK_JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        
        'version': {'type': 'number', 'minimum': 0, 'maximum': 255},
        'prev': {'type': 'string', 'pattern': HASH_HEXLIFY_REGEX},
        'hash': {'type': 'string', 'pattern': HASH_HEXLIFY_REGEX},
        'timestamp': {'type': 'integer', 'minimum': 0},
        'difficulty': {'type': 'integer', 'minimum': 0},
        'nonce': {'type': 'string', 'pattern': HEXSTRING_REGEX},

        'txs': {
            'type': 'array',
            'items': TX_JSON_SCHEMA,
            'minItems': 0
        }

    },
    'required': ['version', 'prev', 'hash', 'timestamp', 'difficulty', 'nonce', 'txs']
}

def is_schema_valid(json_data: dict, schema: dict) -> bool:
    '''
    Verify the schema of a given JSON object
    *** There is no context why the check failed here ***

    Args:
        json_data (dict): JSON Object to check
        schema (dict): Schema to verify on the JSON obj

    Returns:
        bool: Validity of JSON object
    '''

    try:
        #print(json_data)
        validate(json_data, schema)
        return True
    except ValidationError as e:
        #print('\n================================\n', e, '\n============================\n')
        return False

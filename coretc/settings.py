
from dataclasses import dataclass

@dataclass
class ChainSettings:
    debug_stdout_enabled: bool  = True
    debug_fileout_enabled:bool  = True

    debug_log_dir: str          = './data/debug/'
    block_data_directory: str   = './data/blocks/'
    utxo_set_path: str          = './data/utxos.dat'
    mempool_path: str           = './data/mempool.dat'

    block_size_limit: int       = 1024 * 1024   # In bytes (Default = 1MB)
    blocks_per_store_file: int  = 32            # TODO: When done testing this should be 512

    target_blocktime: int       = 10            # In seconds. Set to 300 when done

    initial_blockreward: float  = 10.           
    initial_difficulty: int     = 0x2000FFFF

    difficulty_adjustment: int  = 32 # Every how many blocks is difficulty adjusted, when done this should be 512 (same as blocks per store file)


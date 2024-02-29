
import logging
import logging.config
from rich.logging import RichHandler
from rich.text import Text

# Will improve the logging setup at some point, loading from a json file
# Using rich with logging: https://rich.readthedocs.io/en/latest/logging.html
# Most of the following logging setup is boilerplate from there

FORMAT = f"<%(name)s> %(message)s"

logging.basicConfig(
    level = 'NOTSET', format = FORMAT, datefmt = "[%X]", handlers=[RichHandler()] 
)

logger = logging.getLogger("tc-core")

from coretc.settings import ChainSettings

from coretc.blocks import Block
from coretc.transaction import TX
from coretc.utxo import UTXO
from coretc.utxoset import UTXOSet
from coretc.miner import mine_block

from coretc.chain import Chain, ForkBlock
from coretc.status import BlockStatus
from coretc.wallet import Wallet

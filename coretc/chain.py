
from typing import List

from coretc.blocks import Block
from coretc.status import BlockStatus

class Chain:

    def __init__(self, initDifficulty: int = 0x200000FF):
        
        self.difficulty = initDifficulty
        self.blocks: List[Block] = [] 

    def add_block(self, newBlock: Block) -> BlockStatus:
        '''
        Try to add a new block in the current chain

        Args:
            newBlock (Block): New block to add

        Return:
            BlockStatus: Status enum, indicates possible errors

        '''

        prevhash = self.get_tophash()

        if not newBlock.previous_hash == prevhash:
            return BlockStatus.INVALID_PREVHASH
        
        if not newBlock.difficulty_bits == self.difficulty:
            return BlockStatus.INVALID_DIFFICULTY

        if not newBlock.is_hash_valid():
            return BlockStatus.INVALID_POW

        self.blocks.append(newBlock)

        return BlockStatus.VALID
        
    def get_current_difficulty(self) -> int:
        '''
        Return the current difficulty bits of the chain

        Return:
            int: Difficulty bits
        '''
        
        return self.difficulty

    def get_tophash(self) -> bytes:
        '''
        Return the current top hash or zero-hash if the chain is empty

        Return:
            bytes: 32 byte hash digest

        '''

        return self.blocks[-1].hash_sha256() if len(self.blocks) > 0 else b'\x00'*32

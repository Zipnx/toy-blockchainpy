# TODO

> Shouldve had a separate todo file from the start.

## Core

- [ ] Clean this shit up & tests for TXs
- [ ] Cache the block storage
- [ ] Improve error handling

## Node & RPC

- [ ] Get the peers of peer nodes and process them for usage
- [ ] When a node starts up, notify peers of being online now
- [ ] Penalize peers that cause too many errors / spam
- [ ] During block propagation, send the height along the new block, incase syncing is needed
- [ ] [BUG] Make it so a node cannot have itself as a peer 
- [ ] [BUG] Sometimes the node rejects valid blocks (thats what past me wrote down idk)

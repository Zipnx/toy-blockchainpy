# TODO

> Shouldve had a separate todo file from the start.

## Core

- [ ] Clean this shit up & tests for TXs
- [ ] Cache the block storage
- [ ] Improve error handling
- [ ] Use jsonschema validation, the current system is braindead
- [ ] Test cases for json schema validation
- [ ] [PERFORMANCE] Check the difference in speed between old and new json validation (NOTE: If a block is validated it might not be necessary to validate the json data inside it, due to how i've set this up)

## Node & RPC

- [ ] Get the peers of peer nodes and process them for usage
- [ ] When a node starts up, notify peers of being online now
- [ ] Penalize peers that cause too many errors / spam
- [ ] During block propagation, send the height along the new block, incase syncing is needed
- [ ] [BUG] Make it so a node cannot have itself as a peer 
- [ ] [BUG] Sometimes the node rejects valid blocks (thats what past me wrote down idk)

## Dashboard

> Making a dashboard at some point could be fun. Also showing a graph of nodes

## Wallet

> Making just a small PoC CLI or GUI wallet would also be nice

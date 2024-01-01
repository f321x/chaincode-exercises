# RPC Scavenger Hunt

These exercises require a synced mainnet full node with the transaction index
active (`-txindex=1`). Chaincode Labs can provide credentials to a hosted node
with an authenticated [proxy](https://github.com/pinheadmz/rpc-auth-proxy)
so students can complete the exercises using `bitcoin-cli` locally but without
needing to sync a full node themselves.

Every question must be answered by providing a bash script that executes `bitcoin-cli`
commands. No other commands should be necessary besides bash operators and `jq`.

A good place to start is `bitcoin-cli help` and then `bitcoin-cli help <command name>`.


## Scavenger hunt questions


1. How many new outputs were created by block 123,456?

2. Which tx in block 424,356 spends the coinbase output of block 424,243?

3. Only one single output remains unspent from block 123,321. What address is it sent to?

4. Create a 1-of-4 P2SH multisig address from the public keys in the four inputs of this tx:
  - `37d966a263350fe747f1c606b159987545844a493dd38d84b070027a895c4517`

5. Which public key signed input 0 in this tx:
  - `e5969add849689854ac7f28e45628b89f7454b83e9699e551ce14b6f90c86163`

6. Using descriptors, compute the 100th taproot address dervied from this extended public key:
  - `xpub6Cx5tvq6nACSLJdra1A6WjqTo1SgeUZRFqsX5ysEtVBMwhCCRa4kfgFqaT2o1kwL3esB1PsYr3CUdfRZYfLHJunNWUABKftK2NjHUtzDms2`


## Example:

*How many transactions are confirmed in block 666,666?*

Using local full node:

```sh
hash=$(bitcoin-cli getblockhash 666666)
block=$(bitcoin-cli getblock $hash)
echo $block | jq .nTx
```

Using proxy:

```sh
alias bcli="bitcoin-cli -rpcconnect=34.172.95.104 -rpcuser=a_plus_student -rpcpassword=hunter2"
hash=$(bcli getblockhash 666666)
block=$(bcli getblock $hash)
echo $block | jq .nTx
```

* Note that by saving a `bitcoin.conf` file with these RPC parameters, they
will not need to be added to every command to use the proxy.

Answer: `2728`

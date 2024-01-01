#!/bin/bash

# get coinbase output
block_hash=$(bitcoin-cli getblockhash 424243)
coinbase_tx_id=$(bitcoin-cli getblock $block_hash | jq -r '.tx[0]')

# get spending transaction
block_hash=$(bitcoin-cli getblockhash 424356)
block_info=$(bitcoin-cli getblock $block_hash)
transactions=($(echo $block_info | jq -r '.tx[]'))

for tx in "${transactions[@]}"; do
    txids=$(bitcoin-cli getrawtransaction $tx true | jq -r '.vin[] | .txid')
    for txid in $txids; do
        if [ "$txid" == "$coinbase_tx_id" ]; then
            echo $tx
            exit
        fi
    done
done

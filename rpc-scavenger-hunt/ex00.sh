#!/bin/bash

blockheight=123456
new_utxo_count=0

block_hash=$(bitcoin-cli getblockhash $blockheight)
block_info=$(bitcoin-cli getblock $block_hash)
transactions=($(echo $block_info | jq -r '.tx[]'))

for tx in "${transactions[@]}"; do
	vouts=$(bitcoin-cli getrawtransaction $tx true | jq -r '.vout | length')
	((new_utxo_count += $vouts))
done

echo $new_utxo_count
# or bitcoin-cli getblockstats 123456 | jq ".outs" ??

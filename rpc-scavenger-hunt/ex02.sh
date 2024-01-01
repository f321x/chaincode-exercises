#!/bin/bash

# Only one single output remains unspent from block 123,321. What address is it sent to?

blockheight=123321

block_hash=$(bitcoin-cli getblockhash $blockheight)
block_info=$(bitcoin-cli getblock $block_hash)
transactions=($(echo $block_info | jq -r '.tx[]'))

for tx in "${transactions[@]}"; do
	tx_outputs=$(bitcoin-cli getrawtransaction $tx true | jq ".vout[]" | jq ".n")
	for output in $tx_outputs; do
		utxo_info=$(bitcoin-cli gettxout $tx $output)
		if [ "$utxo_info" != "" ]; then
			echo $utxo_info | jq -r ".scriptPubKey.address"
			exit
		fi
	done
done

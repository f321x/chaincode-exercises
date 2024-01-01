#!/bin/bash
#
#       Create a 1-of-4 P2SH multisig address from the public keys in the four inputs of this tx:
#       37d966a263350fe747f1c606b159987545844a493dd38d84b070027a895c4517

txid=37d966a263350fe747f1c606b159987545844a493dd38d84b070027a895c4517

raw_tx=$(bitcoin-cli getrawtransaction $txid true)
vins=($(echo $raw_tx | jq -c '.vin[]'))

# echo ${vins[@]}

for vin in ${vins[@]};
do
	pubkeys+=($(echo $vin | jq -r '.txinwitness[1]'))
done

json_array=$(jq --compact-output --null-input '$ARGS.positional' --args -- "${pubkeys[@]}")

# echo $json_array

echo $(bitcoin-cli createmultisig 1 $json_array | jq -r '.address')

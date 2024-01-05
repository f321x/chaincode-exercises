#!/bin/bash

# 5. Which public key signed input 0 in this tx:
#   `e5969add849689854ac7f28e45628b89f7454b83e9699e551ce14b6f90c86163`

txid="e5969add849689854ac7f28e45628b89f7454b83e9699e551ce14b6f90c86163"

tx=$(bitcoin-cli getrawtransaction $txid true)
witness=$(echo $tx | jq -r '.vin[0]' | jq -r '.txinwitness[2]')
decoded_redeem_script=$(bitcoin-cli decodescript $witness | jq -r '.asm')

redeem_script_array=$(echo $decoded_redeem_script | jq -R 'split(" ")')
second_string=$(echo $redeem_script_array | jq -r '.[1]')
echo $second_string

# echo -e "\nSpending condition for input: \n"$decoded_redeem_script "\n"

blockhash_in=$(echo $tx | jq -r '.blockhash')
blockheight_in=$(bitcoin-cli getblock $blockhash_in | jq -r '.height')
# echo -e "Blockheight input:" $blockheight_in

txid_output=$(echo $tx | jq -r '.vin[0].txid')
tx_output_hash=$(bitcoin-cli getrawtransaction $txid_output true | jq -r .blockhash)
blockheight_output=$(bitcoin-cli getblock $tx_output_hash | jq -r '.height')
# echo -e "Blockheight output: "$blockheight_output

# echo -e "Blockheight difference:" $(($blockheight_in - $blockheight_output)) "\n"
# echo -e "Pubkey must be 025d524ac7ec6501d018d322334f142c7c11aa24b9cffec03161eca35a1e32a71f as OP_ELSE won't be satisfied\n"




#!/bin/bash

# 6. Using descriptors, compute the 100th taproot address dervied from this extended public key:
#   - `xpub6Cx5tvq6nACSLJdra1A6WjqTo1SgeUZRFqsX5ysEtVBMwhCCRa4kfgFqaT2o1kwL3esB1PsYr3CUdfRZYfLHJunNWUABKftK2NjHUtzDms2`

XPUB=xpub6Cx5tvq6nACSLJdra1A6WjqTo1SgeUZRFqsX5ysEtVBMwhCCRa4kfgFqaT2o1kwL3esB1PsYr3CUdfRZYfLHJunNWUABKftK2NjHUtzDms2

DESCRIPTOR=$(bitcoin-cli getdescriptorinfo "tr($XPUB/0/*)" | jq -r '.descriptor')

# echo $DESCRIPTOR

ADDRESS=$(bitcoin-cli deriveaddresses "$DESCRIPTOR" "[99,99]")

echo $ADDRESS | jq -r '.[0]'

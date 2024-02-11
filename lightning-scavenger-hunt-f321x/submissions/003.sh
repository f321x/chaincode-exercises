#!/bin/bash

# Build the route
route=$(lncli -n "signet" buildroute --amt 4793 --hops "0325ecd6d2d8739681e2f7644f4221ed942b76d6b7825d4e730671ad17fb0d50e5,0324b10f41493935f35cd3b4c1131c94e8f83bfe66c6ebf842790e59e182076d30" --outgoing_chan_id "6243027022577666" --payment_addr "3d93a046e66cf4729498d8c4b3218af89f75dfa21a76851ad002790acc1197b4")
#  "payment_addr": "3d93a046e66cf4729498d8c4b3218af89f75dfa21a76851ad002790acc1197b4",
echo $route
echo ""
# Extract the payment hash from the invoice
# payment_hash=$(lncli -n "signet" decodepayreq --pay_req "lntbs47930n1pjm0s08pp5vu0at7aape3hfg0xnnvdnaxqy9h4xt7pg8a9mhmj38dh09wm57mqdqswaskcmr9w30nzvphcqzzsxq9pyagqsp58kf6q3hxdn6899ycmrztxgv2lz0hthazrfmg2xksqfus4nq3j76q9qyyssq7t3dmyq0yfzv0t05ahtsw0e6gln3gxzh4qccxegg4ehkgls7gfgh23ahk529r70ysgxjc5czuaqgc6j6khfr9x3afff2guvx846327gpf29xa9" | jq -r '.payment_hash')
# echo $payment_hash
#  hash: 671fd5fbbd0e6374a1e69cd8d9f4c0216f532fc141fa5ddf7289db7795dba7b6
# Send the payment over the route
# lncli -n "signet" sendtoroute --payment_hash=671fd5fbbd0e6374a1e69cd8d9f4c0216f532fc141fa5ddf7289db7795dba7b6 --routes=$route

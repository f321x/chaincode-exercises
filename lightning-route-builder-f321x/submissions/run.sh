#!/bin/bash
# Check if three arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <input_file_path> <payment_request_hex> <current_block_height>"
    exit 1
fi

# Assign arguments to variables
input_file_path="$1"
payment_request_hex="$2"
current_block_height="$3"

# Please fill in the version of the programming language you used here to help us with debugging if we run into problems!
version="GO 1.21.5"

# Check if the 'version' variable is not null
if [ -z "$version" ]; then
    echo "Please fill in the version of the programming language you used."
    exit 1
fi

# Your run command here:

(cd solution && go run solution.go $input_file_path $payment_request_hex $current_block_height)

# /workspaces/chaincode-exercises/lightning-route-builder-f321x/test/input.csv 'lnbcrt2m1pju8yyypp5fw792f22sn3fkf7v6s9ts8qqp4pctwrxh2lngsjjd04meyqrqt6sdqqcqzpgxqyz5vqsp5hlfxjuve42lf8ha2unuhta2e3uxr9v37yvr72w7gwm3tllqj56ps9qyyssqjuu0dyg9eny69pcf5nfzax97sx8ewg2dhp05ucr3l3j9dqc7xcw8js7zhw0wz3yg55j8ykkw8hrpv7zvgkwuckhr6q3vsva5y8flf9cqatkpp3' 1000

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
cd route_builder_go_step3
go run main_step3.go $input_file_path $payment_request_hex $current_block_height

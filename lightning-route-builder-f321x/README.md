# Lightning Payment Route Builder

Payments in the lightning network use a series of HTLCs (hash time locked 
contracts) to send bitcoin across the network of payment channels - from a 
sending node to a receiving node. At each hop along the route, the HTLC that 
is added to the payment channel specifies the amount that is being paid (if a 
valid preimage is presented) and the absolute blockchain height at which the 
HTLC will expire. For a given route, these values are selected by applying the 
routing policies that each hop advertises which outline the fee that they 
charge for forwarding and the expiry delta (between incoming and outgoing 
HTLCs) that they require.

For this exercise, you will be required to write a program that produce the 
HTLC values for a given route. 

Note that: 
- This exercise does not require access to a bitcoin or lightning node to 
  complete. 
- This is *not* a pathfinding exercise, the input provided is the selected path.

## Task 

Write a program in a language of your choosing that:
- Accepts three arguments: 
  - 0: an absolute path to a csv file containing a set of hops in a lightning 
       network route.
  - 1: a bech32-encoded regtest payment request, which provides the details of 
       the payment to be made over the route.
  - 2: the current block height, expressed as a uint32.
- Uses the routing policies of the hops provided to produce the values for the 
  HTLCs that will be used to make a payment for the amount and block height 
  provided.
- Outputs the HTLC values for each hop to `stdout`, using the format that is 
  described below.

This assignment is broken down into stages, starting with a basic route and 
adding complexity as the stages progress. To accommodate this, some of the 
inputs/outputs will be hardcoded in the beginning. You should write a single 
program that extends functionality as you progress thorough the steps. The 
output of your final program should be as described in step 3.

You *may* use external libraries to parse payment requests, but must write your
own code for calculation of paths in the route and TLV encoding (in step 3).

Your solution should: 
* Calculate fees [as described in bolt7](https://github.com/lightning/bolts/blob/master/07-routing-gossip.md#htlc-fees), 
  using integer division.
* Obtain payment details (such as payment amount and minimum final 
  CLTV delta) from the payment request.
* May assume that payment requests will always have a non-zero amount 
  specified.

## Step 1 - Simple Route

For this step, you will create for a simple payment route that uses a single 
HTLC.

### Input Format

The input file for your program will specify the hops for payment route that 
you will need to build, separated by newlines. The first hop in the file is 
a channel that is connected to your node, and the last hop is a channel that 
is connected to the destination node. 

The CSV will have the following fields: 
* `path_id`: a `uint32`, hardcoded to `0` for this step.
* `channel_name`: a `string` identifying the channel.
* `cltv_delta`: a `uint32` representing the required delta for the hop.
* `base_fee_msat`: a `uint64` fee expressed in millisatoshis charged per-htlc 
   that uses the channel as an _outgoing_ hop.
* `proportional_fee_ppm`: a `uint64` representing the parts per million 
  proportional fee on the htlc's amount charged to use the channel as an 
  _outgoing_ hop.

#### Example Input: 

Given a simple route where Alice is sending a payment to Dave over the 
following topology:

`Alice (sending node) -- Bob -- Carol -- Dave (receiving node)`

The input CSV file will have the following structure: 
```
path_id,channel_name,cltv_delta,base_fee_msat,proportional_fee_ppm
0,AliceBob,40,1000,10
0,BobCarol,65,2000,500
0,CarolDave,15,0,3000
```

Note that column headings *will* be included for the input file.

Each channel in the lightning network has two forwarding policies, one for each 
direction, advertised by each node. For simplicity, we have only included the 
policies in the direction that your payment will be propagated. 

The example input above represents the following [channel_update](https://github.com/lightning/bolts/blob/master/07-routing-gossip.md#the-channel_update-message)
policies being advertised: 
* Alice requires a `cltv_delta`=40, `fee_base_msat`=1000 and 
  `fee_proportional_millionths`=10 to forward HTLCs over her channel with Bob.
* Bob requires a `cltv_delta`=65, `fee_base_msat`=2000 and 
  `fee_proportional_millionths`=500 to forward HTLCs over his channel with Carol.
* Carol requires a `cltv_delta`=15, `fee_base_msat`=0 and 
  `fee_proportional_millionths`=3000 to forward HTLCs over her channel with Dave.

### Output Format

Your program will be expected to output each hop of the constructed route to 
`stdout` with the following values:
* `path_id`: a `uint32`, hardcoded to `0` for this step.
* `channel_name`: the `string` identifying the channel.
* `htlc_amount_msat`: a `uint64` representing the htlc amount on that channel.
* `htlc_expiry`: a `uint32` representing the expiry height of the htlc.
* `tlv`: a `string`, hardcoded to `NULL`

For the example above, your output should have the following format: 
```
0,AliceBob,amount,expiry,NULL
0,BobCarol,amount,expiry,NULL
0,CarolDave,amount,expiry,NULL
```

Note that you do not need to include CSV headings in your output, but you 
*must trim all whitespace*.

## Step 2 - MPP Route

For this step, you will create a payment route that uses multiple HTLCs to 
pay a single payment. This is called a "multi-part payment", and is often used 
in the network today to break up large payments to improve their chances of 
successfully propagating through the network.

### Input Format

The `path_id` input variable that was hardcoded in the previous exercise will 
be set to represent the various paths your multi-part payment should take. 
You must *split the payment amount equally between the number of paths provided
in the input file*. You may assume that the payment amount will always be 
divisible by the number of paths.

#### Example Input: 

Given the following routes that Alice will use to pay dave over the following 
topology: 

```
Alice (sending node) -- Bob -- Carol -- Dave (receiving node)
Alice (sending node) -- Eve -- Dave (receiving node)
Alice (sending node) -- Fred -- George -- Dave (receiving node)
```

The input CSV file will have the following structure: 
```
path_id,channel_name,cltv_delta,base_fee_msat,proportional_fee_ppm
0,AliceBob,40,1000,10
0,BobCarol,65,2000,500
0,CarolDave,15,0,3000
1,AliceEve,20,5000,20
1,EveDave,40,15,2500
2,AliceFred,50,1000,50
2,FredGeorge,20,1000,0
2,GeorgeDave,45,10000,10
```

If provided an invoice of 120 satoshis, your solution should send 40 satoshis 
over each of these paths (not including fees).

### Output Format

Your output should set the `path_id` field for the paths you have calculated 
to correspond with the values provided in the input file. Hops must be in-order, 
and the file should have the same `path_id` ordering as the input file 
(ascending).

For the example above, your output should have the following format.
```
0,AliceBob,amount,expiry,NULL
0,BobCarol,amount,expiry,NULL
0,CarolDave,amount,expiry,NULL
1,AliceEve,amount,expiry,NULL
1,EveDave,amount,expiry,NULL
2,AliceFred,amount,expiry,NULL
2,FredGeorge,amount,expiry,NULL
2,GeorgeDave,amount,expiry,NULL
```

## Step 3 - TLV Values

The lightning protocol uses [type length value (TLV)](https://github.com/lightning/bolts/blob/master/01-messaging.md#type-length-value-format)
encoded fields to flexibly extend the protocol's functionality. These values 
can optionally be included at any hop in a lightning payment.

For MPP payments, we include a `payment_data` TLV with the following 
information *in the last hop of each path*: 
* A 32 byte `payment_secret` (called a `payment_address` in LND)
* A `uint64` `total_msat` field which contains the total amount being paid
  *across all HTLCs*

Both of these values can be obtained from the payment request that is provided 
as an argument.

The TLV is specified as follows:
```
type [uint64]: 8
length [uint64]: 40

values [40 bytes]:
  32 bytes: payment_secret
  8 bytes: uint64 total_msat
```

Note: for the purposes of this exercise we will use simplified (less efficient).
The actual [specification](https://github.com/lightning/bolts/blob/8a64c6a1cef979b3f0cecb00ba7a48c2d28b3588/04-onion-routing.md#packet-structure)
of this record uses [big size](https://github.com/lightning/bolts/blob/master/01-messaging.md#fundamental-types) 
encoding to save space on the wire.

*Do not include a MPP field* for inputs that only make a payment over 
a single path.

### Input Format

The input format for this step is unchanged from the previous one.

For the purposes of this example, assume that the payment address and total 
amount are as follows:
* `payment_secret`: `b3c3965128b05c96d76348158f8f3a1b92e2847172f9adebb400a9e83e62f066` (hex encoded)
* `total_msat`: 120
    
### Output Format

Your output should update the `tlv` string to include the hex-encoded TLV that 
should be included with the MPP payment. Hops that do not require an additional
tlv payload should still have NULL values.

```
0,AliceBob,amount,expiry,NULL
0,BobCarol,amount,expiry,NULL
0,CarolDave,amount,expiry,00000000000000080000000000000028b3c3965128b05c96d76348158f8f3a1b92e2847172f9adebb400a9e83e62f0660000000000000078
1,AliceEve,amount,expiry,NULL
1,EveDave,amount,expiry,00000000000000080000000000000028b3c3965128b05c96d76348158f8f3a1b92e2847172f9adebb400a9e83e62f0660000000000000078
2,AliceFred,amount,expiry,NULL
2,FredGeorge,amount,expiry,NULL
2,GeorgeDave,amount,expiry,00000000000000080000000000000028b3c3965128b05c96d76348158f8f3a1b92e2847172f9adebb400a9e83e62f0660000000000000078
```

## Assessment

There is **no autograder** to check the validity of your solution for 
this assignment. There are two tests included with the assignment: 
* Sanity check: a basic check that your [run.sh](submissions/run.sh) 
  is working.
* Done: a test that **intentionally fails** until you update 
  [done.sh](submissions/done.sh) to signal that your assignment is 
  ready for manual grading.
  * You must only fix this test **when you are ready to be graded**, 
    you will not get a second chance at submission.

## Submission

Once you have completed the steps, submit the following to the 
[submissions](/submissions) folder:

* The source code for your solution.
* Bash script in [run.sh](/submissions/run.sh) that will run your program 
  with the arguments provided. 
  * Expect this script to be run from within the [submissions](/submissions) 
    directory, i.e: `./run.sh {input.csv path} {payment_request} {height}`
  with the arguments provided.
* When you are satisfied with your solution, follow the instruction in 
  [done.sh](submissions/done.sh) to signal that you are ready for 
  manual assessment.


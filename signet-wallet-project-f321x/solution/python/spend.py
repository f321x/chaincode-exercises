import hashlib
import pickle # for state cache
import os # for state cache
from ecdsa import SigningKey, SECP256k1, util
from typing import List
from balance import (
    EXTENDED_PRIVATE_KEY,
    bcli,
    get_pub_from_priv,
    get_p2wpkh_program,
    recover_wallet_state)


STATE_FILE = "state.pkl"

if os.path.exists(STATE_FILE):
    # Load the state from the file
    with open(STATE_FILE, "rb") as f:
        state = pickle.load(f)
else:
    # Get the state and save it to the file
    state = recover_wallet_state(EXTENDED_PRIVATE_KEY)
    with open(STATE_FILE, "wb") as f:
        pickle.dump(state, f)

# Given 2 compressed public keys as byte arrays, construct
# a 2-of-2 multisig output script. No length byte prefix is necessary.
def create_multisig_script(keys: List[bytes]) -> bytes:
    assert len(keys) == 2
    output_script = bytes.fromhex("52")  # OP_2
    for key in keys:
        output_script += bytes.fromhex("21")  # 33 bytes
        output_script += key
    output_script += bytes.fromhex("52ae")  # OP_2 OP_CHECKMULTISIG
    return output_script


# Given an output script as a byte array, compute the p2wsh witness program
# This is a segwit version 0 pay-to-script-hash witness program.
# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#p2wsh
def get_p2wsh_program(script: bytes, version: int=0) -> bytes:
    version_byte = version.to_bytes(1, "little")
    # Compute the SHA256 hash of the script
    hash256  = hashlib.new("sha256", script).digest()
    # Prepend the version byte and return
    return version_byte + hash256

# Given an outpoint, return a serialized transaction input spending it
# Use hard-coded defaults for sequence and scriptSig
def input_from_utxo(txid: bytes, index: int) -> bytes:
    # Reverse the txid hash so it's little-endian
    reversed_txid = txid[::-1]
    # Index of the output being spent (zero-indexed)
    index = index.to_bytes(4, "little")
    outpoint = reversed_txid + index
    # ScriptSig (empty)
    scriptsig_len = bytes.fromhex("00")
    # Sequence (default)
    sequence = bytes.fromhex("ffffffff")
    # Return the full input
    return outpoint, reversed_txid + index + scriptsig_len + sequence

# Given an output script and value (in satoshis), return a serialized transaction output
def output_from_options(script: bytes, value: int) -> bytes:
    value = value.to_bytes(8, "little")
    script_length = len(script).to_bytes(1, "little")
    return value + script_length + script

# Given a JSON utxo object, extract the public key hash from the output script
# and assemble the p2wpkh scriptcode as defined in BIP143
# <script length> OP_DUP OP_HASH160 <pubkey hash> OP_EQUALVERIFY OP_CHECKSIG
# https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki#specification
def get_p2wpkh_scriptcode(utxo: object) -> bytes:
    asm = utxo["scriptPubKey"]["asm"]
    # Split the script into tokens
    tokens = asm.split(" ")
    # The last token is the pubkey hash
    pubkey_hash = bytes.fromhex(tokens[-1])
    # Assemble the scriptcode
    scriptcode = bytes.fromhex("1976a914") + pubkey_hash + bytes.fromhex("88ac")
    return scriptcode


# Compute the commitment hash for a single input and return bytes to sign.
# This implements the BIP 143 transaction digest algorithm
# https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki#specification
# We assume only a single input and two outputs,
# as well as constant default values for sequence and locktime
#   Double SHA256 of the serialization of:
#      1. nVersion of the transaction (4-byte little endian)
#      2. hashPrevouts (32-byte hash)
#      3. hashSequence (32-byte hash)
#      4. outpoint (32-byte hash + 4-byte little endian)
#      5. scriptCode of the input (serialized as scripts inside CTxOuts)
#      6. value of the output spent by this input (8-byte little endian)
#      7. nSequence of the input (4-byte little endian)
#      8. hashOutputs (32-byte hash)
#      9. nLocktime of the transaction (4-byte little endian)
#     10. sighash type of the signature (4-byte little endian)
def get_commitment_hash(outpoint: bytes, scriptcode: bytes, value: int, outputs: List[bytes]) -> bytes:
    def dsha256(data: bytes) -> bytes:
        return hashlib.new("sha256", hashlib.new("sha256", data).digest()).digest()
    result = b""
    # Version
    result += (2).to_bytes(4, "little")

    # All TX input outpoints (only one in our case)
    result += dsha256(outpoint)  # hashPrevouts
    # All TX input sequences (only one for us, always default value)
    result += dsha256(bytes.fromhex("ffffffff"))
    # Single outpoint being spent (32-byte hash + 4-byte little endian)
    result += outpoint

    # Scriptcode (the scriptPubKey in/implied by the output being spent, see BIP 143) (serialized as scripts inside CTxOuts)
    # Passed scriptcode: scriptcode = bytes.fromhex("1976a914") + pubkey_hash + bytes.fromhex("88ac")
    result += scriptcode

    # Value of output being spent (8-byte little endian)
    result += value.to_bytes(8, "little")
    # Sequence of output being spent (always default for us) (4-byte little endian)
    result += bytes.fromhex("ffffffff")
    # All TX outputs (4-byte little endian)
    # hashOutputs is the double SHA256
    # of the serialization of all output amount (8-byte little endian)
    # with scriptPubKey (serialized as scripts inside CTxOuts)
    result += dsha256(b"".join(outputs))

    # Locktime (always default for us) (4-byte little endian)
    result += bytes.fromhex("00000000")
    # SIGHASH_ALL (always default for us) (4-byte little endian)
    result += bytes.fromhex("01000000")
    return dsha256(result)

# Given a JSON utxo object and a list of all of our wallet's witness programs,
# return the index of the derived key that can spend the coin.
# This index should match the corresponding private key in our wallet's list.
def get_key_index(utxo: object, programs: List[str]) -> int:
    # Get the pubkey hash from the output script
    asm = utxo["scriptPubKey"]["asm"]
    # Split the script into tokens
    tokens = asm.split(" ")
    # The last token is the pubkey hash
    pubkey_hash = tokens[-1]
    # Find the index of the pubkey hash in our list of witness programs
    return programs.index(pubkey_hash)


# Given a private key and message digest as bytes, compute the ECDSA signature.
# Bitcoin signatures:
# - Must be strict-DER encoded
# - Must have the SIGHASH_ALL byte (0x01) appended
# - Must have a low s value as defined by BIP 62:
#   https://github.com/bitcoin/bips/blob/master/bip-0062.mediawiki#user-content-Low_S_values_in_signatures
def sign(priv: bytes, msg: bytes) -> bytes:
    # Create a signing object from the private key
    sk = SigningKey.from_string(priv, curve=SECP256k1)
    # Sign the message digest
    sig = sk.sign_digest(msg, sigencode=util.sigencode_der_canonize)
    # Append the SIGHASH_ALL byte
    # Decode the DER-encoded signature
    # vk = sk.get_verifying_key()
    r, s = util.sigdecode_der(sig, SECP256k1.order)
    # Extract the s value
    # If the s value is too high, negate it
    if s > SECP256k1.order // 2:
        s = SECP256k1.order - s
    # Re-encode the signature
    sig = util.sigencode_der(r, s, SECP256k1.order)
    sig += bytes.fromhex("01")
    return sig
    # Keep signing until we produce a signature with "low s value"
    # We will have to decode the DER-encoded signature and extract the s value to check it
    # Format: 0x30 [total-length] 0x02 [R-length] [R] 0x02 [S-length] [S] [sighash]


# Given a private key and transaction commitment hash to sign,
# compute the signature and assemble the serialized p2pkh witness
# as defined in BIP 141 (2 stack items: signature, compressed public key)
# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#specification
def get_p2wpkh_witness(priv: bytes, msg: bytes) -> bytes:
    # Get the compressed public key
    pub = get_pub_from_priv(priv)
    # Compute the signature
    sig = sign(priv, msg)
    # Assemble the witness
    witness = bytes.fromhex("00") + sig + pub
    return witness

# Given two private keys and a transaction commitment hash to sign,
# compute both signatures and assemble the serialized p2pkh witness
# as defined in BIP 141
# Remember to add a 0x00 byte as the first witness element for CHECKMULTISIG bug
# https://github.com/bitcoin/bips/blob/master/bip-0147.mediawiki
def get_p2wsh_witness(privs: List[bytes], msg: bytes) -> bytes:
    # Get the compressed public keys
    pubs = [get_pub_from_priv(priv) for priv in privs]
    # Compute the signatures
    sigs = [sign(priv, msg) for priv in privs]
    # Assemble the witness
    witness = bytes.fromhex("00")
    for sig in sigs:
        witness += sig
    for pub in pubs:
        witness += pub
    return witness


# Given arrays of inputs, outputs, and witnesses, assemble the complete
# transaction and serialize it for broadcast. Return bytes as hex-encoded string
# suitable to broadcast with Bitcoin Core RPC.
# https://en.bitcoin.it/wiki/Protocol_documentation#tx
def assemble_transaction(inputs: List[bytes], outputs: List[bytes], witnesses: List[bytes]) -> str:
    version = (2).to_bytes(4, "little")
    marker = bytes.fromhex("00")
    flags = bytes.fromhex("0001")
    locktime = bytes.fromhex("00000000")
    tx = b""
    tx += version + marker + flags + len(inputs).to_bytes(1, "little")

    for input in inputs:
        tx += input

    tx += len(outputs).to_bytes(1, "little")
    for output in outputs:
        tx += output

    for witness in witnesses:
        tx += witness

    tx += locktime
    return tx.hex()

# Given arrays of inputs and outputs (no witnesses!) compute the txid.
# Return the 32 byte txid as a *reversed* hex-encoded string.
# https://developer.bitcoin.org/reference/transactions.html#raw-transaction-format
def get_txid(inputs: List[bytes], outputs: List[bytes]) -> str:
    version = (2).to_bytes(4, "little")
    locktime = bytes.fromhex("00000000")
    tx = b""
    tx += version + len(inputs).to_bytes(1, "little")
    for input in inputs:
        tx += input
    tx += len(outputs).to_bytes(1, "little")
    for output in outputs:
        tx += output
    tx += locktime
    return hashlib.new("sha256", hashlib.new("sha256", tx).digest()).digest()[::-1].hex()


# Spend a p2wpkh utxo to a 2 of 2 multisig p2wsh and return the txid
def spend_p2wpkh(state: object) -> str:
    FEE = 1000
    AMT = 1000000
    input = {}
    index = 0
    # Choose an unspent coin worth more than 0.01 BTC
    for txid, utxo in state["utxo"].items():  # maybe need to check if utxo even is a p2wpkh
        if utxo[1] > AMT + FEE:
            input['txid'] = txid  # txid
            input['op_index'] = utxo[0]  # outpoint index
            input['value_sats'] = utxo[1]  # value in satoshis
            input['utxo_obj'] = utxo[2]   # utxo object
            input['priv_key_index'] = index
            break
        index += 1

    # Create the input from the utxo
    # Reverse the txid hash so it's little-endian
    op, serialized_input = input_from_utxo(bytes.fromhex(input['txid']), input["op_index"])

    # Compute destination output script and output
    pubkeys = [bytes.fromhex(state["pubs"][0]), bytes.fromhex(state["pubs"][1])]
    musig_script = create_multisig_script(pubkeys)
    output_musig = output_from_options(musig_script, AMT)

    # Compute change output script and output
    change_script = get_p2wpkh_program(bytes.fromhex(state["pubs"][0]))
    change_output = output_from_options(change_script, input["value_sats"] - AMT - FEE)

    # Get the message to sign
    scriptcode = get_p2wpkh_scriptcode(input["utxo_obj"])
    msg = get_commitment_hash(op, scriptcode, input["value_sats"], [output_musig, output_from_options(change_script, input["value_sats"] - AMT - FEE)])

    # Fetch the private key we need to sign with
    priv = state["privs"][input["priv_key_index"]]
    # Sign!
    witness = get_p2wpkh_witness(priv, msg)

    # Assemble
    final = assemble_transaction([serialized_input], [output_musig, change_output], [witness])

    # Reserialize without witness data and double-SHA256 to get the txid
    txid = get_txid([serialized_input], [output_musig, change_output])
    # For debugging you can use RPC `testmempoolaccept ["<final hex>"]` here
    return txid, final


# state = recover_wallet_state(EXTENDED_PRIVATE_KEY)
print(spend_p2wpkh(state))

# Spend a 2-of-2 multisig p2wsh utxo and return the txid
# def spend_p2wsh(state: object, txid: str) -> str:
#     COIN_VALUE = 1000000
#     FEE = 1000
#     AMT = 0
#     # Create the input from the utxo
#     # Reverse the txid hash so it's little-endian

#     # Compute destination output script and output

#     # Compute change output script and output

#     # Get the message to sign

#     # Sign!

#     # Assemble

#     # For debugging you can use RPC `testmempoolaccept ["<final hex>"]` here
#     return finalhex


# https://mempool.btcfoss.bitherding.com/
# if __name__ == "__main__":
#     # Recover wallet state: We will need all key pairs and unspent coins
#     state = recover_wallet_state(EXTENDED_PRIVATE_KEY)
#     txid1, tx1 = spend_p2wpkh(state)
#     print(tx1)
#     tx2 = spend_p2wsh(state, txid1)
#     print(tx2)

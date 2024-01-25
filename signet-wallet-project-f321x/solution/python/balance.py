from decimal import Decimal
from ecdsa import SigningKey, SECP256k1
from subprocess import run
from typing import List, Tuple
import hashlib
import hmac
import json

# Provided by administrator
WALLET_NAME = "wallet_107"
DESCRIPTOR="wpkh(tprv8ZgxMBicQKsPf4ey4o4mdpUh3AYy7JA5vySudZ8boXjFhYYjJ9TrP5FPiqhiAh8jPcPi4zMJ2FkdPgnzXDogMy8uoEAWDBVDrRAzyz8J7Dz/84h/1h/0h/0/*)#2d6m058e"
EXTENDED_PRIVATE_KEY = "tprv8ZgxMBicQKsPf4ey4o4mdpUh3AYy7JA5vySudZ8boXjFhYYjJ9TrP5FPiqhiAh8jPcPi4zMJ2FkdPgnzXDogMy8uoEAWDBVDrRAzyz8J7Dz"

# don't understand this yet.  need to read more about it
# def verify_checksum(xprv_bytes: bytes) -> bool:
#     # Compute the checksum
#     checksum = hashlib.sha256(hashlib.sha256(xprv_bytes).digest()).digest()[:4]
#     # Verify the checksum
#     return checksum == xprv_bytes[-4:]

# Decode a base58 string into an array of bytes
def base58_decode(base58_string: str) -> bytes:
    base58_alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    big_integer = 0
    index = 0
    # Convert Base58 string to a big integer
    for char in base58_string:
        big_integer *= 58
        big_integer += base58_alphabet.index(char)
    # Convert the integer to bytes
    byte_length = (big_integer.bit_length() + 7) // 8
    xprv_bytes = big_integer.to_bytes(byte_length, "big")
    return xprv_bytes[:-4]

# base58_decode(EXTENDED_PRIVATE_KEY)


# This 78 byte structure can be encoded like other Bitcoin data in Base58, by first adding 32 checksum bits (derived from the double SHA-256 checksum), and then converting to the Base58 representation. This results in a Base58-encoded string of up to 112 characters. Because of the choice of the version bytes, the Base58 representation will start with "xprv" or "xpub" on mainnet, "tprv" or "tpub" on testnet.
# Deserialize the extended key bytes and return a JSON object
# https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#serialization-format
# 4 byte: version bytes (mainnet: 0x0488B21E public, 0x0488ADE4 private; testnet: 0x043587CF public, 0x04358394 private)
# 1 byte: depth: 0x00 for master nodes, 0x01 for level-1 derived keys, ....
# 4 bytes: the fingerprint of the parent's key (0x00000000 if master key)
# 4 bytes: child number. This is ser32(i) for i in xi = xpar/i, with xi the key being serialized. (0x00000000 if master key)
# 32 bytes: the chain code
# 33 bytes: the public key or private key data (serP(K) for public keys, 0x00 || ser256(k) for private keys)
def deserialize_key(b: bytes) -> object:
    data_dict = {
        "version": b[:4],
        "depth": b[4],
        "parent_fingerprint": b[5:9],
        "child_number": b[9:13],
        "chain_code": b[13:45],
        "key": b[45:],
    }
    return data_dict



# Derive the secp256k1 compressed public key from a given private key
# BONUS POINTS: Implement ECDSA yourself and multiply you key by the generator point!
def get_pub_from_priv(priv: bytes) -> bytes:
    secret_obj = SigningKey.from_string(priv, curve=SECP256k1)
    pub_bytes = secret_obj.get_verifying_key().to_string("compressed")
    # pub_bytes = secret_obj.get_verifying_key().to_string()
    return pub_bytes


# Perform a BIP32 parent private key -> child private key operation
# Return a JSON object with "key" and "chaincode" properties as bytes
# https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki#user-content-Private_parent_key_rarr_private_child_key
def derive_priv_child(key: bytes, chaincode: bytes, index: int, hardened: bool) -> object:
    # If so (hardened child): let I = HMAC-SHA512(Key = cpar, Data = 0x00 || ser256(kpar) || ser32(i)).
    # (Note: The 0x00 pads the private key to make it 33 bytes long.)
    if hardened:
        index += 0x80000000
        I = hmac.new(chaincode, b'\x00' + key + int(index).to_bytes(4, 'big'), hashlib.sha512).digest()
    # If not (normal child): let I = HMAC-SHA512(Key = cpar, Data = serP(point(kpar)) || ser32(i)).
    else:
        I = hmac.new(chaincode, get_pub_from_priv(key) + int(index).to_bytes(4, 'big'), hashlib.sha512).digest()
    IL, IR = I[:32], I[32:]
    key_int = int.from_bytes(key, 'big')
    IL_int = int.from_bytes(IL, 'big')
    child_key_int = (key_int + IL_int) % SECP256k1.order
    child_key = child_key_int.to_bytes(32, 'big')
    result_dict = {
        "key": child_key,
        "chaincode": IR
    }
    return result_dict


# Given an extended private key and a BIP32 derivation path,
# compute the first 2000 child private keys.
# Return an array of keys encoded as bytes.
# The derivation path is formatted as an array of (index: int, hardened: bool) tuples.
def get_wallet_privs(key: bytes, chaincode: bytes, path: List[Tuple[int, bool]]) -> List[bytes]:
    privs = []
    for index, hardened in path[:-1]:
        child = derive_priv_child(key, chaincode, int(index), hardened)
        key = child["key"]
        chaincode = child["chaincode"]
    index = int(path[-1][0])
    hardened = path[-1][1]
    while len(privs) < 2001:
        child = derive_priv_child(key, chaincode, index, hardened)
        privs.append(child["key"])
        index += 1
    return privs


# Derive the p2wpkh witness program (aka scriptPubKey) for a given compressed public key.
# Return a bytes array to be compared with the JSON output of Bitcoin Core RPC getblock
# so we can find our received transactions in blocks.
# These are segwit version 0 pay-to-public-key-hash witness programs.
# https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#user-content-P2WPKH
def get_p2wpkh_program(pubkey: bytes, version: int=0) -> bytes:
    # 0x00 for mainnet, 0x01 for testnet
    # return version.to_bytes(1, 'big') + hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    pubkey_hash = hashlib.new('ripemd160', hashlib.sha256(pubkey).digest()).digest()
    return version.to_bytes(1, 'big') + len(pubkey_hash).to_bytes(1, 'big') + pubkey_hash


# Assuming Bitcoin Core is running and connected to signet using default datadir,
# execute an RPC and return its value or error message.
# https://github.com/bitcoin/bitcoin/blob/master/doc/bitcoin-conf.md#configuration-file-path
# Examples: bcli("getblockcount")
#           bcli("getblockhash 100")
def bcli(cmd: str):
    res = run(
            ["bitcoin-cli", "-signet"] + cmd.split(" "),
            capture_output=True,
            encoding="utf-8")
    if res.returncode == 0:
        return res.stdout.strip()
    else:
        raise Exception(res.stderr.strip())

# DESCRIPTOR="wpkh(tprv8ZgxMBicQKsPf4ey4o4mdpUh3AYy7JA5vySudZ8boXjFhYYjJ9TrP5FPiqhiAh8jPcPi4zMJ2FkdPgnzXDogMy8uoEAWDBVDrRAzyz8J7Dz/84h/1h/0h/0/*)#2d6m058e"
def parse_path_from_descriptor(descriptor: str) -> List[Tuple[int, bool]]:
    path = []
    index = 0

    while (descriptor[index] != "/"):
        index += 1
    if (descriptor[index] == "/"):
        index += 1
        while (descriptor[index] != ")"):
            current_index = ""
            if (descriptor[index].isdigit()):
                while (descriptor[index].isdigit()):
                    current_index += str(descriptor[index])
                    index += 1
                if (descriptor[index] == "h"):
                    current_tuple = (str(current_index) , True)
                else:
                    current_tuple = (str(current_index) , False)
                path.append(current_tuple)
            index += 1
    return (path)


def parse_xpriv_from_descriptor(descriptor: str) -> str:
    xprv = ""
    index = 0

    while (descriptor[index] != "("):
        index += 1
    index += 1
    while (descriptor[index] != "/"):
        xprv += descriptor[index]
        index += 1
    return xprv

# Recover the wallet state from the blockchain:
# - Parse xprv and path from descriptor and derive 2000 key pairs and witness programs
# - Request blocks 0-310 from Bitcoin Core via RPC and scan all transactions
# - Return a state object with all the derived keys and total wallet balance
# data_dict = {
#     "version": b[:4],
#     "depth": b[4],
#     "parent_fingerprint": b[5:9],
#     "child_number": b[9:13],
#     "chain_code": b[13:45],
#     "key": b[45:],
# }
def recover_wallet_state(xprv: str):
    path = parse_path_from_descriptor(DESCRIPTOR)

    path.append((0, False)) # add to parsing function

    xprv = base58_decode(parse_xpriv_from_descriptor(DESCRIPTOR))

    des_key = deserialize_key(xprv)

    if (des_key["key"][0] == 0):
        des_key["key"] = des_key["key"][1:]

    privs = get_wallet_privs(des_key['key'], des_key['chain_code'], path)

    pubs_hex = []
    programs_hex = []
    for priv in privs:
        pub = get_pub_from_priv(priv)
        pubs_hex.append(pub.hex())
        programs_hex.append(get_p2wpkh_program(pub).hex())

    state = {
        "utxo": {},
        "balance": 0,
        "privs": privs,
        "pubs": pubs_hex,
        "programs": programs_hex
    }

    height = 310
    for h in range(height + 1):
        txs = json.loads(bcli(f"getblock {bcli(f'getblockhash {h}')} 2"), parse_float=Decimal)["tx"]
        # Scan every tx in every block
        for tx in txs:
            # # Check every tx output for our own witness programs.
            # # These are coins we have received.
            for out in tx["vout"]:
                scriptPubKey = out.get("scriptPubKey")
                scPubKeyHex = scriptPubKey.get("hex")
                if scPubKeyHex != None and scPubKeyHex in programs_hex:
                    # state["balance"] += out["value"]
                    value_satoshis = int(out["value"] * 100000000)
                    state["utxo"][tx["txid"]] = [out["n"], value_satoshis]

            # # Check every tx input (witness) for our own compressed public keys.
            # # These are coins we have spent.
            for inp in tx["vin"]:
                txinwitness = inp.get("txinwitness")
                if txinwitness != None and len(txinwitness) > 1:
                    if txinwitness[1] in pubs_hex:
                        if inp.get("txid") in state["utxo"]:
                            if (inp.get("vout") == state["utxo"][inp.get("txid")][0]):
                                del state["utxo"][inp.get("txid")]

            # Remove this coin from our wallet state utxo pool
            # so we don't double spend it later
            # Add to our total balance
    for txid, out in state["utxo"].items():
        state["balance"] += out[1]
    state["balance"] = state["balance"] / 100000000.0
    # print(state["balance"])
    return state

# bitcoin-cli scantxoutset "start" '["wpkh(tprv8ZgxMBicQKsPf4ey4o4mdpUh3AYy7JA5vySudZ8boXjFhYYjJ9TrP5FPiqhiAh8jPcPi4zMJ2FkdPgnzXDogMy8uoEAWDBVDrRAzyz8J7Dz/84h/1h/0h/0/*)#2d6m058e"]'
#   "total_amount": 16.01713376 probably?
if __name__ == "__main__":
    print(f"{WALLET_NAME} {recover_wallet_state(EXTENDED_PRIVATE_KEY)['balance']}")

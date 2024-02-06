def parse_mempool_csv():
    """Parse the CSV file and return a list of MempoolTransactions."""
    mempool = {}
    with open('mempool.csv') as f:
        for line in f.readlines():
            line_elements = line.strip().split(',')
            tx = {
                "fee": int(line_elements[1]),
                "weight": int(line_elements[2]),
                "parents": line_elements[3].split(';') if line_elements[3] else None
            }
            mempool[line_elements[0]] = tx
    return mempool


def add_parent_weight(mempool, child):
    parent_weight = 0
    if not mempool[child]["parents"]:
        return mempool[child]["weight"]
    for parent in mempool[child]["parents"]:
        parent_weight += add_parent_weight(mempool, parent)
    return parent_weight


def add_parent_fee(mempool, child):
    parent_fee = 0
    if not mempool[child]["parents"]:
        return mempool[child]["fee"]
    for parent in mempool[child]["parents"]:
        parent_fee += add_parent_fee(mempool, parent)
    return parent_fee


def calculate_packet_values(mempool):
    for tx in mempool:
        if mempool[tx]["parents"] is not None:
           mempool[tx]["packet_weight"] += add_parent_weight(mempool, tx)
           mempool[tx]["packet_fee"] += add_parent_fee(mempool, tx)
           mempool[tx]["packet_feerate"] = mempool[tx]["packet_fee"] / mempool[tx]["packet_weight"]


def set_packet_weights(mempool):
    for tx in mempool.values():
        tx["packet_weight"] = tx["weight"]
        tx["packet_fee"] = tx["fee"]
        tx["packet_feerate"] = tx["fee"] / tx["weight"]

def get_block_size(block):
    block_weight = 0
    for tx_content in block.values():
        block_weight += tx_content["weight"]
    return block_weight


def add_parents_to_block(block, mempool, child):
    if child not in mempool:
        return block, mempool
    if not mempool[child]["parents"]:
        block[child] = mempool[child]
        del mempool[child]
        return
    for parent in mempool[child]["parents"]:
        add_parents_to_block(block, mempool, parent)
    block[child] = mempool[child]
    del mempool[child]
    return

def build_block(mempool):
    block = {}
    while (get_block_size(block) < 4000000):
        add_parents_to_block(block, mempool, list(mempool.keys())[0])
        mempool = dict(sorted(mempool.items(), key=lambda item: item[1]["packet_feerate"], reverse=True))
    while (get_block_size(block) > 4000000):
        block.popitem()
    return block

def write_block_to_file(block, filename):
    with open(filename, 'w') as f:
        for txid, tx in block.items():
            parent_txids = '' if tx['parents'] is None else ';'.join(tx['parents'])
            f.write(f"{txid},{tx['fee']},{tx['weight']},{parent_txids}\n")

def run_checks(block):
    if get_block_size(block) > 4000000:
        raise Exception("Block too big!")

def main():
    mempool = parse_mempool_csv()
    set_packet_weights(mempool)
    calculate_packet_values(mempool)
    mempool = dict(sorted(mempool.items(), key=lambda item: item[1]["packet_feerate"], reverse=True))
    block = build_block(mempool)
    run_checks(block)
    write_block_to_file(block, 'block.txt')

main()

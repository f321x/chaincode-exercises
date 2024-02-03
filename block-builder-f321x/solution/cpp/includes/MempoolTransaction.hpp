#pragma once

#include <iostream>
#include <vector>
#include <sstream>
#include <cstdlib>
#include <string>

class MempoolTransaction {
	public:
		MempoolTransaction(void);
		MempoolTransaction(std::string read_line);
		~MempoolTransaction();

	private:
		std::vector<std::string>	_parents;
		std::string 				_txid;
		int 						_fee_sats;
		int 						_weight;

		void _parse_line(const std::string& read_line);
};

// class MempoolTransaction():
//     def __init__(self, txid, fee, weight, parents):
//         self.txid = txid
//         self.fee = int(fee)
//         # TODO: add code to parse weight and parents fields

// def parse_mempool_csv():
//     """Parse the CSV file and return a list of MempoolTransactions."""
//     with open('mempool.csv') as f:
//         return [MempoolTransaction(*line.strip().split(',')) for line in f.readlines()]

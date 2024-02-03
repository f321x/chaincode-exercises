#include "main.hpp"

static std::vector<MempoolTransaction> read_mempool_csv(const std::string &file_path) {
	std::vector<MempoolTransaction> transactions;
	std::ifstream file(file_path.c_str());
	std::string line;

	if (!file.is_open()) {
		std::cerr << "Error: Mempool file not found" << std::endl;
		exit(1);
	}
	if (file.is_open()) {
		while (std::getline(file, line)) {
			transactions.push_back(MempoolTransaction(line));
		}
	}
	return transactions;
}

int main() {
	std::vector<MempoolTransaction> transactions = read_mempool_csv("mempool.csv");

	return 0;
}

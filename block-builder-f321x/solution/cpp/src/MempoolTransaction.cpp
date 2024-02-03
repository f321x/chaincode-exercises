#include "MempoolTransaction.hpp"

MempoolTransaction::MempoolTransaction(void) { }

MempoolTransaction::MempoolTransaction(std::string read_line) {
	_parse_line(read_line);
}

MempoolTransaction::~MempoolTransaction() { }

void	MempoolTransaction::_parse_line(const std::string& read_line) {
	std::string token;
	std::stringstream ss(read_line);
	std::vector<std::string> tokens;

	while (std::getline(ss, token, ',')) {
		tokens.push_back(token);
	}
	if (tokens.size() > 4 || tokens.size() < 3) {
		std::cerr << "Invalid input in mempool.csv :\n"
		<< read_line << std::endl;
		exit(1);
	}
	// ss << tokens[0];
	// ss >> _txid;
	// ss << tokens[1];
	// ss >> _fee_sats;
	// ss << tokens[2];
	// ss >> _weight;

    std::stringstream	parents_stream(tokens[3]);
    std::string			parent;

    while (std::getline(parents_stream, parent, ';')) {
        _parents.push_back(parent);
    }
}

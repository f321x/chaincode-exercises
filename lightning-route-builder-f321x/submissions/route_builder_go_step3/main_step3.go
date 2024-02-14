package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"strconv"

	decodepay "github.com/f321x/ln-decodepay"
)

type Route struct {
	path_id              uint32
	channel_name         string
	cltv_delta           uint32
	base_fee_msat        uint64
	proportional_fee_ppm uint64
}

func parseHops(csv_data [][]string) []Route {
	var routes []Route
	for i, line := range csv_data {
		if i > 0 {
			var rte Route
			var err error
			var tmp uint64

			tmp, err = strconv.ParseUint(line[0], 10, 32)
			if err != nil {
				log.Fatal(err)
			}
			rte.path_id = uint32(tmp)
			rte.channel_name = line[1]
			tmp, err = strconv.ParseUint(line[2], 10, 32)
			if err != nil {
				log.Fatal(err)
			}
			rte.cltv_delta = uint32(tmp)
			rte.base_fee_msat, err = strconv.ParseUint(line[3], 10, 64)
			if err != nil {
				log.Fatal(err)
			}
			rte.proportional_fee_ppm, err = strconv.ParseUint(line[4], 10, 64)
			if err != nil {
				log.Fatal(err)
			}
			routes = append(routes, rte)
		}
	}
	return routes
}

func checkError(err error) {
	if err != nil {
		log.Fatal(err)
	}
}

// Expected stdout (example):
// 0,AliceBob,amount,expiry,NULL

func calc_fee_for_hop(current_route Route, val_msat uint64) uint64 {
	var fee_msat uint64

	fee_msat += current_route.base_fee_msat
	fee_msat += (val_msat * current_route.proportional_fee_ppm) / 1000000
	return fee_msat
}

func calculate_tlv(payment_secret string, total_msat uint64) string {
	typeHex := fmt.Sprintf("%016x", 8)
	lengthHex := fmt.Sprintf("%016x", 40)

	// Convert totalMsat to hex string
	totalMsatHex := fmt.Sprintf("%016x", total_msat)

	// Concatenate type, length, and values
	tlv := typeHex + lengthHex + payment_secret + totalMsatHex

	return tlv
}

func calc_routes(bolt11_amnt uint64, routes []Route, block_height uint32, path_index int, multi_hop bool, bolt11 decodepay.Bolt11) []string {
	var result []string
	var all_fees uint64
	var tlv string

	for index, channel := range routes {
		if index > 0 && channel.path_id == uint32(path_index) {
			all_fees += calc_fee_for_hop(channel, bolt11_amnt)
		}
	}
	if multi_hop {
		tlv = calculate_tlv(bolt11.PaymentAddr, uint64(bolt11.MSatoshi))
	}
	for index, channel := range routes {
		if channel.path_id == uint32(path_index) {
			block_height += channel.cltv_delta
			if index > 0 {
				all_fees -= calc_fee_for_hop(channel, bolt11_amnt)
			}
			if (((index < len(routes) - 1) && routes[index + 1].path_id != channel.path_id) || index == len(routes) - 1) && multi_hop {
				current_htlc := fmt.Sprintf("%d,%s,%d,%d,%s", channel.path_id, channel.channel_name,
				all_fees+bolt11_amnt, block_height, tlv)
				result = append(result, current_htlc)
			} else {
				current_htlc := fmt.Sprintf("%d,%s,%d,%d,NULL", channel.path_id, channel.channel_name,
				all_fees+bolt11_amnt, block_height)
				result = append(result, current_htlc)
			}
		}
	}
	return result
}

func multi_hop_payment(route []Route, block_height uint32, bolt11 decodepay.Bolt11) []string {
	var path_amnt int
	var end_result []string
	multi_hop := false

	for _, channel := range route {
		if channel.path_id > uint32(path_amnt) {
			path_amnt = int(channel.path_id)
		}
	}
	path_amnt += 1
	if path_amnt > 1 {
		multi_hop = true
	}
	total_amnt := bolt11.MSatoshi
	hop_sum := total_amnt / int64(path_amnt)
	for i := 0; i < path_amnt; i++ {
		index_routes := calc_routes(uint64(hop_sum), route, block_height, i, multi_hop, bolt11)
		end_result = append(end_result, index_routes...)
	}
	return end_result
}

func main() {
	args := os.Args[1:]
	var routes []Route

	if len(args) != 3 {
		log.Fatal("Wrong amount of arguments! (1) CSV | (2) bech32 | (3) current block height [uint32]")
	}
	csv_file, err := os.Open(args[0])
	checkError(err)

	csvReader := csv.NewReader(csv_file)
	data, err := csvReader.ReadAll()
	checkError(err)

	defer csv_file.Close()
	routes = parseHops(data)

	bolt11, error := decodepay.Decodepay(args[1])
	checkError(error)

	// overwrite bolt11 with hardcoded variables for exercise 3
	// bolt11.PaymentAddr = "b3c3965128b05c96d76348158f8f3a1b92e2847172f9adebb400a9e83e62f066"
	// bolt11.MSatoshi = 120
	// fmt.Println(bolt11.PaymentAddr)
	block_height, err := strconv.ParseUint(args[2], 10, 32)
	checkError(err)
	result_strings := multi_hop_payment(routes, uint32(block_height), bolt11)
	for _, hop := range result_strings {
		fmt.Println(hop)
	}
}

// Bolt11{
// 	MSatoshi:           msat,
// 	PaymentHash:        hex.EncodeToString(inv.PaymentHash[:]),
// 	Description:        desc,
// 	DescriptionHash:    deschash,
// 	Payee:              hex.EncodeToString(inv.Destination.SerializeCompressed()),
// 	CreatedAt:          int(inv.Timestamp.Unix()),
// 	Expiry:             int(inv.Expiry() / time.Second),
// 	MinFinalCLTVExpiry: int(inv.MinFinalCLTVExpiry()),
// 	Currency:           inv.Net.Bech32HRPSegwit,
// 	Route:              routes,
// }

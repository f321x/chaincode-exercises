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

func checkError(err error) {
	if err != nil {
		log.Fatal(err)
	}
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

func fee_calculation(current_path []Route, val_msat uint64) []uint64 {
	var fees []uint64
	var reversed_fees []uint64

	for i := len(current_path) - 1; i > 0; i-- {
		var calculated_fees uint64 = 0
		calculated_fees += current_path[i].base_fee_msat
		calculated_fees += (val_msat + sum64(fees)) * current_path[i].proportional_fee_ppm / 1000000
		if calculated_fees == 0 {
			calculated_fees = 1
		}
		calculated_fees += sum64(fees)
		fees = append(fees, calculated_fees)
	}
	for i := len(fees) - 1; i >= 0; i-- {
		reversed_fees = append(reversed_fees, fees[i])
	}
	reversed_fees = append(reversed_fees, 0)
	return reversed_fees
}

func calc_fees(routes []Route, val_msat uint64) []uint64 {
	var current_path_id []Route
	var all_fees []uint64

	for i, route := range routes {
		current_path_id = append(current_path_id, route)
		if last_one(routes, i) {
			all_fees = append(all_fees, fee_calculation(current_path_id, val_msat)...)
			current_path_id = []Route{}
		}
	}
	// fmt.Println("all fees: ", all_fees)
	return all_fees
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

func sum(numbers []uint32) uint32 {
	var sum uint32

	for _, number := range numbers {
		sum += number
	}
	return sum
}

func sum64(numbers []uint64) uint64 {
	var sum uint64

	for _, number := range numbers {
		sum += number
	}
	return sum
}

func last_one(routes []Route, i int) bool {
	curr_path_id := routes[i].path_id

	if i+1 < len(routes) && routes[i+1].path_id != curr_path_id {
		return true
	}
	if i+1 == len(routes) {
		return true
	}
	return false
}

// calculates the cltv deltas for all hops and stores it in an uint32 array
func calc_cltv_deltas(routes []Route, bolt11 decodepay.Bolt11, block_height uint32) []uint32 {
	var result []uint32
	min_ex := bolt11.MinFinalCLTVExpiry

	for i := 0; i < len(routes); {
		current_path_id := routes[i].path_id
		tmp_i := i
		var total_delta uint32 = 0

		// Accumulate CLTV deltas for the current path
		for i < len(routes) && routes[i].path_id == current_path_id {
			if last_one(routes, i) && routes[i].cltv_delta < uint32(min_ex) {
				total_delta += uint32(min_ex)
			} else {
				total_delta += routes[i].cltv_delta
			}
			i++
		}
		// Append the accumulated delta to the result slice.
		i = tmp_i + 1
		result = append(result, total_delta+block_height)
	}
	return result
}

func calc_routes(bolt11_amnt uint64, routes []Route, block_height uint32, path_index int, multi_hop bool, bolt11 decodepay.Bolt11) []string {
	var result []string
	var all_fees []uint64
	var tlv string

	if multi_hop {
		tlv = calculate_tlv(bolt11.PaymentAddr, uint64(bolt11.MSatoshi))
	}
	cltv_deltas := calc_cltv_deltas(routes, bolt11, block_height)
	all_fees = calc_fees(routes, bolt11_amnt)
	for index, channel := range routes {
		if channel.path_id == uint32(path_index) {
			if (((index < len(routes)-1) && routes[index+1].path_id != channel.path_id) || index == len(routes)-1) && multi_hop {
				current_htlc := fmt.Sprintf("%d,%s,%d,%d,%s", channel.path_id, channel.channel_name,
					all_fees[index]+bolt11_amnt, cltv_deltas[index], tlv)
				result = append(result, current_htlc)
			} else {
				current_htlc := fmt.Sprintf("%d,%s,%d,%d,NULL", channel.path_id, channel.channel_name,
					all_fees[index]+bolt11_amnt, cltv_deltas[index])
				result = append(result, current_htlc)
			}
		}
	}
	return result
}

func calc_hop_sums(total int64, paths int) []uint32 {
	var result []uint32

	if total%int64(paths) == 0 {
		for i := 0; i < paths; i++ {
			result = append(result, uint32(total/int64(paths)))
		}
		return result
	} else {
		for i := 0; i < paths-1; i++ {
			result = append(result, uint32(total/int64(paths)))
		}
		result = append(result, uint32(total)-sum(result))
		return result
	}
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
	hop_sums := calc_hop_sums(total_amnt, path_amnt)
	for i := 0; i < path_amnt; i++ {
		index_routes := calc_routes(uint64(hop_sums[i]), route, block_height, i, multi_hop, bolt11)
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

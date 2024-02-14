package main

import (
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"strconv"

	decodepay "github.com/nbd-wtf/ln-decodepay"
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

func calc_routes(bolt11 decodepay.Bolt11, routes []Route, block_height uint32) []string {
	var result []string
	var all_fees uint64

	for index, channel := range routes {
		if index > 0 {
			all_fees += calc_fee_for_hop(channel, uint64(bolt11.MSatoshi))
		}
	}
	for index, channel := range routes {
		block_height += channel.cltv_delta
		if index > 0 {
			all_fees -= calc_fee_for_hop(channel, uint64(bolt11.MSatoshi))
		}
		current_htlc := fmt.Sprintf("0,%s,%d,%d,NULL", channel.channel_name,
			all_fees+uint64(bolt11.MSatoshi), block_height)
		result = append(result, current_htlc)
	}
	return result
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
	block_height, err := strconv.ParseUint(args[2], 10, 32)
	checkError(err)
	result_strings := calc_routes(bolt11, routes, uint32(block_height))
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

/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   wallet.hpp                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: fbock <fbock@student.42heilbronn.de>       +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/01/14 15:06:02 by fbock             #+#    #+#             */
/*   Updated: 2024/01/14 15:33:20 by fbock            ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#pragma once
#include <iostream>
#include <cstddef>

class Wallet {
	public:
		Wallet( std::string extended_priv_key );
		~Wallet( void );

	private:
		const std::string _base58_alphabet =
			"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
		std::string	_xprv;
		std::byte	*to_bytes();
};

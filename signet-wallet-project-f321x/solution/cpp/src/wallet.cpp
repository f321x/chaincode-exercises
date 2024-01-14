/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   wallet.cpp                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: fbock <fbock@student.42heilbronn.de>       +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2024/01/14 15:16:06 by fbock             #+#    #+#             */
/*   Updated: 2024/01/14 15:26:35 by fbock            ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "wallet.hpp"

Wallet::Wallet(std::string extended_priv_key) : _xprv(extended_priv_key) {}

Wallet::~Wallet(void) { }

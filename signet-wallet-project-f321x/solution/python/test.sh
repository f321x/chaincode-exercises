#!/bin/bash





printf "302e0201010420 91ff57bc1b5b80d78c79a95db31d0af410f177a8620da9d697c2b77e739297e2 a00706052b8104000a" | xxd -p -r > priv.hex
openssl ec -inform d < priv.hex > priv.pem
printf "5f534117564be69ec26f519d507a10f6a687904c1da28dcbb27ed7c4abfb2717" | xxd -p -r | sha256sum | xxd -p -r | sha256sum | xxd -p -r > msg
openssl pkeyutl -inkey priv.pem -sign -in msg -pkeyopt digest:sha256 | xxd -p -c256

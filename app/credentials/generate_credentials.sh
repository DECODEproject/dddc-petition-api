#!/usr/bin/env bash

set -e 
set -u
set -o pipefail 
# set -x
# https://coderwall.com/p/fkfaqq/safer-bash-scripts-with-set-euxo-pipefail

pfx=../coconut_contracts

zenroom -z $pfx/credential_keygen.zen | tee keypair.keys
zenroom -k keypair.keys -z $pfx/create_request.zen | tee request.json
zenroom -k issuer_keypair.keys -a request.json -z $pfx/issuer_sign.zen | tee signature.json
zenroom -k keypair.keys -a signature.json -z $pfx/aggregate_signature.zen | tee credentials.json

cp -v keypair.keys ae6b8a1b77a1f67fc76f2e676bae319c451418feaa48af298cab041581a27917.keys
cp -v issuer_keypair.keys ae6b8a1b77a1f67fc76f2e676bae319c451418feaa48af298cab041581a27917.verify
cp -v credentials.json ae6b8a1b77a1f67fc76f2e676bae319c451418feaa48af298cab041581a27917

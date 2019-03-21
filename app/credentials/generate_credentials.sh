#!/usr/bin/env bash

set -e 
set -u
set -o pipefail 
# set -x
# https://coderwall.com/p/fkfaqq/safer-bash-scripts-with-set-euxo-pipefail


zenroom                                                            ../contracts/src/01-CITIZEN-credential-keygen.zencode              > keypair.keys
zenroom -k keypair.keys                                            ../contracts/src/02-CITIZEN-credential-request.zencode             > blind_signature.req
zenroom -k ci_keypair.keys                                         ../contracts/src/04-CREDENTIAL_ISSUER-publish-verifier.zencode     > ci_verify_keypair.keys
zenroom -k ci_keypair.keys            -a blind_signature.req       ../contracts/src/05-CREDENTIAL_ISSUER-credential-sign.zencode      > ci_signed_credential.json
zenroom -k keypair.keys               -a ci_signed_credential.json ../contracts/src/06-CITIZEN-aggregate-credential-signature.zencode > credential.json
zenroom -k credential.json            -a ci_verify_keypair.keys    ../contracts/src/07-CITIZEN-prove-credential.zencode               > blindproof_credential.json
zenroom -k blindproof_credential.json -a ci_verify_keypair.keys    ../contracts/src/08-VERIFIER-verify-credential.zencode
zenroom -k credential.json            -a ci_verify_keypair.keys    ../contracts/src/09-CITIZEN-create-petition.zencode                > petition_request.json
zenroom -k ci_verify_keypair.keys     -a petition_request.json     ../contracts/src/10-VERIFIER-approve-petition.zencode              > petition.json
zenroom -k credential.json            -a ci_verify_keypair.keys    ../contracts/src/11-CITIZEN-sign-petition.zencode                  > petition_signature.json

mv keypair.keys 3b2332e905bd662448d7114d0626421b82deb33fcf3bafe3c284bdfb9f58e2c6.keys
mv ci_verify_keypair.keys 3b2332e905bd662448d7114d0626421b82deb33fcf3bafe3c284bdfb9f58e2c6.verify
mv credential.json 3b2332e905bd662448d7114d0626421b82deb33fcf3bafe3c284bdfb9f58e2c6
rm blind_signature.req ci_keypair.keys ci_signed_credential.json blindproof_credential.json petition_request.json petition.json

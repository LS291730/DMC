#!/bin/bash

#circom circuit.circom --r1cs --wasm --sym
#snarkjs zkey new circuit.r1cs pot14_final.ptau circuit_00.zkey
#snarkjs zkey contribute circuit_00.zkey circuit_01.zkey --name="1st Contributor Name"
#snarkjs zkey beacon circuit_01.zkey circuit_final.zkey 010203 10
#snarkjs zkey export verificationkey circuit_final.zkey verification_key.json
snarkjs groth16 fullprove input.json circuit.wasm circuit_final.zkey proof.json public.json
snarkjs groth16 verify verification_key.json public.json proof.json
#snarkjs zkey export solidityverifier circuit_final.zkey verifier.sol
snarkjs zkey export soliditycalldata public.json proof.json > offchaintransferproof.txt

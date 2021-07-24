#!/bin/bash

#circom circuit.circom --r1cs --wasm --sym
snarkjs powersoftau new bn128 12 pot12_00.ptau
#snarkjs powersoftau contribute pot12_00.ptau pot12_01.ptau --name="First contribution" < random.txt
snarkjs powersoftau contribute pot12_00.ptau pot12_01.ptau --name="First contribution" -e="some random text"

snarkjs powersoftau beacon pot12_01.ptau pot12_beacon.ptau 010203 10
snarkjs powersoftau prepare phase2 pot12_beacon.ptau pot12_final.ptau
snarkjs zkey new circuit.r1cs pot12_final.ptau circuit_00.zkey
#snarkjs zkey contribute circuit_00.zkey circuit_01.zkey --name="1st Contributor Name" < random.txt
snarkjs zkey contribute circuit_00.zkey circuit_01.zkey --name="1st Contributor Name" -e="some random text"
snarkjs zkey beacon circuit_01.zkey circuit_final.zkey 010203 10
snarkjs zkey export verificationkey circuit_final.zkey verification_key.json
snarkjs groth16 fullprove input.json circuit.wasm circuit_final.zkey proof.json public.json
snarkjs groth16 verify verification_key.json public.json proof.json
#snarkjs zkey export solidityverifier circuit_final.zkey verifier.sol
snarkjs zkey export soliditycalldata public.json proof.json > deposit_proof.txt

import sys
sys.path.append('E:/mixer/')
from web3 import Web3, HTTPProvider
import solcx
from typing import Dict, Union, Any
from back_end.contract import deploy_contract, interact_contract
import json

web3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
DEFAULT_MIX_GAS_WEI = 3000000

def deployContract(contract_source_path: str, contract_name: str):
    deployer_eth_address = web3.eth.accounts[0]
    deployer_eth_private_key = 'de19b0d4c514cb2241eb6fcd54d0880e353119bf4de4d8c07ae7815862deda2c'
    deployment_gas = 3000000
    # deploy contract
    address = deploy_contract(web3, contract_source_path, contract_name, deployer_eth_address, deployer_eth_private_key, 0, deployment_gas)
    print(f'Deployed {contract_name} to: {address}\n')

def deposit_back_end(sender_eth_address: str, sender_eth_private_key: str, transfer_value: int, proof: str) :
    mixer_contract = instantiate_contract()
    # deal with proof to get a, b, c and input
    (a,b,c) = parse_proof(proof)
    input_ = [int(proof[568:634], 16), int(proof[637:703], 16)]
    # call the deposit function of mixer
    contract_call = mixer_contract.functions.deposit(a,b,c,input_)
    (tx_receipt, transaction_contract_ouput) = interact_contract(web3, contract_call, sender_eth_address, sender_eth_private_key, transfer_value, DEFAULT_MIX_GAS_WEI)
    print(transaction_contract_ouput)
    return (tx_receipt, transaction_contract_ouput)

def compute_merkle_path(leaf_index: int):
    mixer_contract = instantiate_contract()
    transaction_contract_ouput = mixer_contract.functions.compute_merkle_path(leaf_index).call()
    # (tx_receipt, transaction_contract_ouput) = interact_contract(web3, contract_call, sender_eth_address, sender_eth_private_key, transfer_value, DEFAULT_MIX_GAS_WEI)
    # print(transaction_contract_ouput)
    return transaction_contract_ouput

def openchannel_back_end(sender_eth_address: str, sender_eth_private_key: str, proof: str) :
    #interact with contract
    mixer_contract = instantiate_contract()
    # deal with proof to get a, b, c and input
    (a,b,c) = parse_proof(proof)
    # public_input=(sn_1, sn_2, drcm, urcm,root)
    input_ = [int(proof[568:634], 16), int(proof[637:703], 16), int(proof[706:772], 16), int(proof[775:841], 16), int(proof[844:910], 16)]
    # call the deposit function of mixer
    contract_call = mixer_contract.functions.open_channel(a,b,c,input_)
    (tx_receipt, transaction_contract_ouput) = interact_contract(web3, contract_call, sender_eth_address, sender_eth_private_key, None, DEFAULT_MIX_GAS_WEI)
    print(transaction_contract_ouput)
    return (tx_receipt, transaction_contract_ouput)

def closechannel_back_end(sender_eth_address, sender_eth_private_key, message_hash, signature, proof, version_number):
    mixer_contract = instantiate_contract()
    # deal with proof to get a, b, c and input
    (a,b,c) = parse_proof(proof)
    # public_input=(sn, urcm1, urcm2,root)
    input_ = [int(proof[568:634], 16), int(proof[637:703], 16), int(proof[706:772], 16), int(proof[775:841], 16)]
    # call the deposit function of mixer
    contract_call = mixer_contract.functions.close_channel(message_hash, signature,a,b,c,input_,version_number)
    (tx_receipt, transaction_contract_ouput) = interact_contract(web3, contract_call, sender_eth_address, sender_eth_private_key, None, DEFAULT_MIX_GAS_WEI)
    print(transaction_contract_ouput)
    return (tx_receipt, transaction_contract_ouput)

def withdraw_back_end(sender_eth_address, sender_eth_private_key, receive_address, proof):
    mixer_contract = instantiate_contract()
    # deal with proof to get a, b, c and input
    (a,b,c) = parse_proof(proof)
    # public_input=(sn, urcm1, urcm2,root)
    input_ = [int(proof[568:634], 16), int(proof[637:703], 16), int(proof[706:772], 16)]
    # call the deposit function of mixer
    contract_call = mixer_contract.functions.withdraw(receive_address,a,b,c,input_)
    (tx_receipt, transaction_contract_ouput) = interact_contract(web3, contract_call, sender_eth_address, sender_eth_private_key, None, DEFAULT_MIX_GAS_WEI)
    # print(transaction_contract_ouput)
    return (tx_receipt, transaction_contract_ouput)


def instantiate_contract():
    contract_name = 'Mixer'
    compiled_contract_path = 'E:/mixer/back_end/compiled_contracts/compiled_Mixer_info.txt'
    with open(compiled_contract_path, 'r') as f:
        contract_info = json.load(f)
        contract_address = contract_info['Mixer_address']
        compiled_contract_abi = contract_info['abi']
    contract = web3.eth.contract(address=contract_address, abi=compiled_contract_abi)
    return contract

def parse_proof(proof):
    # deal with proof to get a, b, c and input
    a = [int(proof[2:68], 16), int(proof[72:138], 16)]
    b = [[int(proof[144:210], 16), int(proof[214:280], 16)], [int(proof[285:351], 16), int(proof[355:421], 16)]]
    c = [int(proof[427:493], 16), int(proof[497:563], 16)]
    return (a,b,c)

if __name__ == "__main__":
    # contract_source_path = 'E:/mixer/back_end/contracts/MerkleTree_MiMC.sol'
    # contract_name = 'MerkleTree_MiMC' 
    # contract_source_path = 'E:/mixer/back_end/contracts/VerifyDeposit.sol'
    # contract_name = 'DepositVerifier' 
    # contract_source_path = 'E:/mixer/back_end/contracts/VerifyOpenChannel.sol'
    # contract_name = 'OpenChannelVerifier' 
    # contract_source_path = 'E:/mixer/back_end/contracts/VerifyOffchainTransfer.sol'
    # contract_name = 'OffchainTransferVerifier' 
    # contract_source_path = 'E:/mixer/back_end/contracts/VerifySignature.sol'
    # contract_name = 'SignatureVerifier' 
    # contract_source_path = 'E:/mixer/back_end/contracts/VerifyWithdraw.sol'
    # contract_name = 'WithdrawVerifier' 
    contract_source_path = 'E:/mixer/back_end/contracts/Mixer.sol'
    contract_name = 'Mixer'  
    deployContract(contract_source_path, contract_name)  

    contract_name = 'Mixer'
    compiled_contract_path = 'E:/mixer/back_end/compiled_contracts/compiled_' + contract_name + '_info.txt'
    proof_path = 'E:/mixer/front_end/zksnarks_proof/depositproof.txt'
    # interactWithContract(compiled_contract_path, contract_name, proof_path)

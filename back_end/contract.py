from web3 import Web3, HTTPProvider
import solcx
from typing import Dict, Union, Any
import json

#deploy contracts
def deploy_contract(web3, contract_source_path, contract_name, deployer_eth_address: str,
            deployer_eth_private_key: str, value: float, deployment_gas: int):
    compiled_contract = compile_contract_source_file(contract_source_path, contract_name)
    contract = web3.eth.contract(abi=compiled_contract['abi'], bytecode=compiled_contract['bin'])
    construct_call = contract.constructor()#*args
    tx_desc: Dict[str, Union[str, int]] = {'from': deployer_eth_address}
    if value:#transfer the unit from ether to wei 
        tx_desc["value"] = Web3.toWei(value, 'ether')
    if deployment_gas:
        tx_desc["gas"] = deployment_gas
    if deployer_eth_private_key:
        tx_desc["gasPrice"] = web3.eth.gasPrice
        tx_desc["nonce"] = web3.eth.getTransactionCount(deployer_eth_address)
        transaction = construct_call.buildTransaction(tx_desc)
        signed_tx = web3.eth.account.signTransaction(transaction, deployer_eth_private_key)
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    contract_address = tx_receipt['contractAddress']
    # deployed_contract_address = 'E:/mixer/back_end/deployed_contract_address.txt'
    compiled_contract_path = 'E:/mixer/back_end/compiled_contracts/compiled_' + contract_name + '_info.txt'
    with open(compiled_contract_path, 'r') as f:
        temp = json.load(f)
        temp[contract_name + '_address'] = contract_address
    with open(compiled_contract_path, 'w') as f:
        json.dump(temp, f)
    return contract_address

def compile_contract_source_file(contract_source_path, contract_name) -> Dict[str, Any]:
    # SOL_COMPILER_VERSION = 'v0.6.11'
    contract_path_list = [contract_source_path]
    # solcx.install_solc(SOL_COMPILER_VERSION)
    # solcx.set_solc_version(SOL_COMPILER_VERSION)
    compiled_all = solcx.compile_files(contract_path_list)#List[str]
    compiled_contract = compiled_all[f"{contract_source_path}:{contract_name}"]
    compiled_contract_path = 'E:/mixer/back_end/compiled_contracts/compiled_' + contract_name + '_info.txt'
    with open(compiled_contract_path, 'w') as f:
        json.dump({'abi': compiled_contract['abi']}, f)
    return compiled_contract
 
def interact_contract(web3, contract_call, sender_eth_address: str,
            sender_eth_private_key: str, value: int, gas: int):
    tx_desc: Dict[str, Union[str, int]] = {'from': sender_eth_address}
    if value:#transfer the unit from ether to wei 
        # tx_desc['value'] = Web3.toWei(value, 'ether')
        tx_desc['value'] = value
    if gas:
        tx_desc['gas'] = gas
    if sender_eth_private_key:
        tx_desc['gasPrice'] = web3.eth.gasPrice
        tx_desc['nonce'] = web3.eth.getTransactionCount(sender_eth_address)
    # transaction = deployed_contract.functions.setVar(web3.toInt(30)).buildTransaction(tx_desc)
    # contract_call = deployed_contract.functions.setVar(web3.toInt(30))
    transaction = contract_call.buildTransaction(tx_desc)
    transaction_contract_ouput = contract_call.call(tx_desc)
    # print('5555555555555555')
    # print(transaction_contract_ouput)
    #两种方法都可以
    # tx_hash = web3.eth.sendTransaction(transaction)
    # tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
    signed_tx = web3.eth.account.signTransaction(transaction, sender_eth_private_key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    print('00000000000000')
    # print(deployed_contract.functions.getVar().call())
    # contract_address = tx_receipt['contractAddress']
    return (tx_receipt, transaction_contract_ouput)
import sys
sys.path.append('E:/mixer/')
from back_end.op_enter import deposit_back_end, openchannel_back_end, closechannel_back_end,withdraw_back_end, compute_merkle_path
from eth_keys import keys
from eth_utils import decode_hex
from Crypto import Random
from hashlib import sha256
from typing import Union, List
from web3 import Web3, HTTPProvider
import json
import os

# Merkle tree depth
MERKLE_TREE_DEPTH: int = 32
# Gas cost estimates
DEPLOYMENT_GAS_WEI: int = MERKLE_TREE_DEPTH * 250000
DEFAULT_MIX_GAS_WEI: int = DEPLOYMENT_GAS_WEI
ZETH_PRIME: int = 21888242871839275222246405745257275088548364400416034343698204186575808495617
# Hash digest length (for commitment and PRFs)
DIGEST_LENGTH: int = 256
web3 = Web3(Web3.HTTPProvider('http://localhost:7545'))

def sk_to_pk_addr(private_key: str):
    # generate public key and address from the given private key
    private_key_bytes = decode_hex(private_key)
    private_key = keys.PrivateKey(private_key_bytes)
    public_key = private_key.public_key
    # uncompressed public key 
    # sender_public_key = public_key.to_hex()
    # compressed public key
    compressed_public_key: str = public_key.to_compressed_bytes().hex()
    # the corresponding address
    address: str = public_key.to_checksum_address()
    return (compressed_public_key, address)

def create_note(sender: str, sender_public_key: str, recipient_public_key, value: int):    
    s_pk: int = int.from_bytes(bytes.fromhex(sender_public_key), byteorder='big',signed=False)
    # compute random r of note
    random_r: int = int.from_bytes(Random.get_random_bytes(32),byteorder='big',signed=False)
    note_dir = 'E:/mixer/front_end/transaction_info/new_notes/'
    note_num = len(os.listdir(note_dir))
    note_num_str = str(note_num)
    # need to store random_r(store the note)
    note_path = note_dir + note_num_str + '_' + sender + '_new_note.txt'
    with open(note_path, 'w') as f:
        note_value = {'sender_pk':s_pk}
        if(recipient_public_key != None):
            r_pk: int = int.from_bytes(bytes.fromhex(recipient_public_key), byteorder='big',signed=False)
            note_value['recipient_pk'] = r_pk
        note_value['v'] = value
        note_value['r'] = random_r
        note_info = {'leaf_value': note_value}
        json.dump(note_info,f) 

#向合约发送交易，转账+承诺+证明，转账值、data(proof+public input)
def deposit(sender_private_key: str, deposit_value: int, deposit_record_path,proof_path):
    (_, sender_address) = sk_to_pk_addr(sender_private_key)

    # no need to compute urcm = commit(pk,v,r)
    # use zkp to generate proof 
    # public_input=(urcm,deposit_value); private_input=(public_key,random_r); out=urcm
    
    # get proof and input
    with open(proof_path, 'r') as f:
        proof = f.read()
    (tx_receipt, deposit_ouput) = deposit_back_end(sender_address, sender_private_key, deposit_value, proof)
    # store leaf_index, leaf_value=(pk,v,r) for generating proof
    with open(deposit_record_path, 'r') as f:
        temp = json.load(f)
        temp['leaf_index'] = deposit_ouput
    with open(deposit_record_path, 'w') as f:
        json.dump(temp, f)
    

# open channel, select two urcm to create a channel between Alice and Bob
def openChannel(sender_private_key: str, note_paths: List, proof_path):
    (_, sender_address) = sk_to_pk_addr(sender_private_key)

    # use zkp to generate proof 
    # public_input=(sn_1,sn_2,drcm,new_urcm,root),private_input=(old_urcm_i,old_note_pk,old_note_v_i,old_note_r_i,new_note_pk,new_note_v_1,new_note_r_1,new_note_v_2,new_note_r_2,sk,path_i)
    
    # get proof and input
    with open(proof_path, 'r') as f:
        proof = f.read()
    (tx_receipt, deposit_ouput) = openchannel_back_end(sender_address, sender_private_key, proof)
    # store leaf_index, leaf_value=(pk,v,r) for generating proof
    for i in range(2):
        with open(note_paths[i], 'r') as f:
            temp = json.load(f)
            temp['leaf_index'] = deposit_ouput[i]
        with open(note_paths[i], 'w') as f:
            json.dump(temp, f)

# use a channel drcm to create two urcms belonging to sender and recipient 
def offChainTransfer(sender_account, offchain_proof_path, version_number):
    # use sender_private_key to sign message=(proof,version)
    # get proof and input
    with open(offchain_proof_path, 'r') as f:
        proof = f.read()
    print(proof)
    proof = proof.replace('\n', '')
    proof = proof.replace('[', '')    
    proof = proof.replace(']', '')
    proof = proof.replace('"', '')    
    # print(proof)
    proof_array = proof.split(',')
    # print(proof_array)
    proof_string = proof_array[0]
    for i in range(1, len(proof_array)):
        proof_string += proof_array[i].strip()[2:]
    # print(proof_string)
    version_number_hex = hex(version_number)
    filled_0 = '0' * (66 - len(version_number_hex))  
    version_number_hex = '0x' + filled_0 + version_number_hex[2:]
    message =  proof_string + version_number_hex[2:]   
    print(message)
    sha3_message = web3.sha3(hexstr=message)
    signed_message = web3.eth.sign(sender_account, sha3_message)
    print(sha3_message.hex())
    print(signed_message.hex())
    offchain_tx_dir = 'E:/mixer/front_end/transaction_info/offchain_transactions/'
    offchain_tx_num = len(os.listdir(offchain_tx_dir))
    offchain_tx_num_str = str(offchain_tx_num)
    # need to store offchain transaction
    offchain_tx_record_path = offchain_tx_dir + offchain_tx_num_str + '_offchain_tx.txt'
    # sender send transfer info to recipient, including proof, public_input, message_hash, signature
    with open(offchain_proof_path, 'r', encoding="utf-8") as f:
        proof_input = f.read()
        offchain_tx_info = {'offchain_proof_input': proof_input}
        offchain_tx_info['version_number'] = version_number
        offchain_tx_info['message_hash'] = sha3_message.hex()
        offchain_tx_info['signature'] = signed_message.hex()
    with open(offchain_tx_record_path, 'w') as f:
        json.dump(offchain_tx_info,f)

# sender/recipient close channel, destory drcm and insert two urcms
# interact with closeChannel function in mixer contract, input include message=(proof,public_input=(sn,urcm1,urcm2,root), version_number),message hash,signature
def closeChannel(sender_private_key, offchain_tx_record_path, note_paths: List,offchain_proof_path):
    (_, sender_address) = sk_to_pk_addr(sender_private_key)

    # use zkp to generate proof 
    # public_input=(sn,urcm_r,urcm_s,root)
    # private_input=(drcm,pk_s,pk_r,v,v1,v2,sk_s,path,r1,r2)
    
    # get proof and input
    with open(offchain_proof_path, 'r') as f:
        proof = f.read()
    with open(offchain_tx_record_path, 'r') as f:
        offchain_tx_record = json.load(f)   
    version_number = offchain_tx_record['version_number']
    message_hash = offchain_tx_record['message_hash']
    signature = offchain_tx_record['signature']
    (tx_receipt, closechannel_ouput) = closechannel_back_end(sender_address, sender_private_key, message_hash, signature, proof, version_number)
    # store leaf_index, leaf_value=(pk,v,r) for generating proof
    for i in range(2):
        with open(note_paths[i], 'r') as f:
            temp = json.load(f)
            temp['leaf_index'] = closechannel_ouput[i]
        with open(note_paths[i], 'w') as f:
            json.dump(temp, f)

# no need to input withdraw_value, because it is in the public input of proof
def withdraw(sender_private_key, receive_address, withdraw_proof_path):
    (_, sender_address) = sk_to_pk_addr(sender_private_key)
    # use zkp to generate proof 
    # public_input=(sn,v,root)
    # private_input=(urcm,pk,sk,r,leaf_index,path)

    # get proof and input
    with open(withdraw_proof_path, 'r') as f:
        proof = f.read()
    (tx_receipt, withdraw_ouput) = withdraw_back_end(sender_address, sender_private_key, receive_address, proof)
    print(withdraw_ouput)


if __name__ == "__main__":

    # deposit: create note when depositing, then generate proof using the note
    sender_account = web3.eth.accounts[1]
    sender_private_key: str = "b06ba45d58ba83d81feae8cb802b2f98f7c063d5573c58ca45f348ff11c6aa61"
    (sender_public_key, _) = sk_to_pk_addr(sender_private_key)
    # print(bytes.fromhex(sender_public_key))
    deposit_value: int = 5
    # create_note('Alice',sender_public_key,None,5)
    # deposit_record_path = 'E:/mixer/front_end/transaction_info/new_notes/0_Alice_new_note.txt'
    # proof_path = 'E:/mixer/front_end/zksnarks_proof/depositproof_1.txt'
    # deposit(sender_private_key, deposit_value,deposit_record_path,proof_path)
    # create_note('Alice',sender_public_key,None,5)
    # deposit_record_path = 'E:/mixer/front_end/transaction_info/new_notes/1_Alice_new_note.txt'
    # proof_path = 'E:/mixer/front_end/zksnarks_proof/depositproof_2.txt'
    # deposit(sender_private_key, deposit_value,deposit_record_path,proof_path)

    # openchannel: create two notes, nullifiers and paths, then generate proof using them
    # compute two new notes
    recipient_account = web3.eth.accounts[2]
    recipient_private_key: str = "f26ed0980370f654788e4e52b06e841bbb5eb0cd9af51467f1a10fd2f268d896"
    (recipient_public_key, recipient_address) = sk_to_pk_addr(recipient_private_key)
    new_note_value_1 = 6
    new_note_value_2 = 4
    # create_note('Alice',sender_public_key,recipient_public_key,new_note_value_1)
    # create_note('Alice',sender_public_key,None,new_note_value_2)
    # use mixer contract to compute path_i from old_urcm_i 
    # path1 = compute_merkle_path(0)
    # path2 = compute_merkle_path(1) 
    # print(path1)
    # print(path2)
    note_path_1 = 'E:/mixer/front_end/transaction_info/new_notes/2_Alice_new_note.txt'
    note_path_2 = 'E:/mixer/front_end/transaction_info/new_notes/3_Alice_new_note.txt'
    note_paths: List = [note_path_1, note_path_2]
    openchannel_proof_path = 'E:/mixer/front_end/zksnarks_proof/openchannelproof.txt'
    # openChannel(sender_private_key, note_paths, openchannel_proof_path)
    
    # transfer off chain
    # create two urcm
    new_note_value_1 = 2
    new_note_value_2 = 4
    # create_note('Bob',recipient_public_key,None,new_note_value_1)
    # create_note('Alice',sender_public_key,None,new_note_value_2)
    # use mixer contract to compute path from drcm
    drcm_leaf_index = 2
    # path = compute_merkle_path(drcm_leaf_index)
    # print(path)
    offchain_proof_path = 'E:/mixer/front_end/zksnarks_proof/offchaintransferproof.txt'
    version_number = 1
    # offChainTransfer(sender_account, offchain_proof_path, version_number)

    offchain_tx_record_path = 'E:/mixer/front_end/transaction_info/offchain_transactions/0_offchain_tx.txt'
    note_path_1 = 'E:/mixer/front_end/transaction_info/new_notes/4_Bob_new_note.txt'
    note_path_2 = 'E:/mixer/front_end/transaction_info/new_notes/5_Alice_new_note.txt'
    note_paths: List = [note_path_1, note_path_2]
    # closeChannel(sender_private_key,offchain_tx_record_path,note_paths,offchain_proof_path)

    receive_address = recipient_address
    # note_path = 'E:/mixer/front_end/transaction_info/4_Bob_tx_record.txt'
    # use mixer contract to compute path from drcm
    urcm_leaf_index = 4
    # path = compute_merkle_path(urcm_leaf_index)
    # print(path)
    withdraw_proof_path = 'E:/mixer/front_end/zksnarks_proof/withdrawproof.txt'
    withdraw(sender_private_key,receive_address, withdraw_proof_path)


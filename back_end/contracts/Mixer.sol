// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.6.11; 

//The two operations deposit and withdraw should be defined in the same contract in the form of functions,
//not respectively in the form of contract——Deposit.sol/Withdraw.sol
//Because different contract have different address, then the coins in two contracts is different.
import "./VerifyDeposit.sol";
import "./MerkleTree_MiMC.sol";
import "./VerifyOpenChannel.sol";
import './VerifySignature.sol';
import './VerifyOffchainTransfer.sol';
import './VerifyWithdraw.sol';

contract Mixer{
    MerkleTree_MiMC merkletree = MerkleTree_MiMC(0x38708fa67583A5c21611E0aac5b47eBf272fBea8);
    DepositVerifier deposit_vf = DepositVerifier(0xE4c1eF3638967c423722cb2dC27Ce7bcf61cc883);
    OpenChannelVerifier openchannel_vf = OpenChannelVerifier(0x13F03BBE7f271472debcbA1024599DBe6613bf55);
    OffchainTransferVerifier offchaintransfer_vf = OffchainTransferVerifier(0xcc4390d877a276F6D65762f3Da596674c0D8a3a3);
    SignatureVerifier signature_vf = SignatureVerifier(0x0Dd2db1433596e40e72EDdFF2f170bB13E48F978);
    WithdrawVerifier withdraw_vf = WithdrawVerifier(0xfE0b7b1050dcB193A7bE46f0EA81B4124D510E8c);
    
    uint constant DEPTH = 5;
    // The roots of the different updated trees
    mapping(uint256 => bool) private _roots;

    // The public list of nullifiers (prevents double spend)
    mapping(uint256 => bool) private _nullifiers;
    
    // The merkle tree 
    // MerkleTree_MiMC merkletree = new MerkleTree_MiMC();
    
    event print_transfer_value(uint);
    event print_transaction_value(uint);
    event Log_path(uint[5]);
    event LogNodes(uint256[63] );
    event Log_root(uint);
    //
    function deposit(uint[2] memory a, uint[2][2] memory b, uint[2] memory c, uint[2] memory public_input) public payable returns (uint leaf_index) {
        //There is no need verifying transaction signature, which is done by the Ethereum mechanism
        //1. verify the transfer_value in public_input is equal to msg.value 
        //public_input = (urcm, transfer_value)
        uint transfer_value = public_input[1];
        emit print_transfer_value(transfer_value);
        emit print_transaction_value(msg.value);
        require(msg.value == transfer_value, "msg.value is not equal to the transfer_value");
        //2. verify proof
        bool re = deposit_vf.verifyProof(a, b, c, public_input);
        require(re, "the verification of deposit proof is not passed");
        //3. if proof is correct, then add urcm and update merkle tree root
        uint urcm = public_input[0];
        // compute leaf index
        leaf_index = merkletree.num_leaves();
        // insert into merkle tree
        merkletree.insert(urcm);
        // compute the root of merkle root
        uint256 new_merkle_root = merkletree.computeRoot(leaf_index);
        emit Log_root(new_merkle_root);
        _roots[new_merkle_root] = true;
        // uint[3] memory path = merkletree.compute_merkle_path(0);
        // emit Log_path(path);
     }
    
    function open_channel(uint[2] memory a, uint[2][2] memory b, uint[2] memory c, uint[5] memory public_input) public returns(uint[2] memory){
        //public_input: sn_1, sn_2, drcm, urcm, root
        uint sn_1 = public_input[0];
        uint sn_2 = public_input[1];
        uint drcm = public_input[2];
        uint urcm = public_input[3];
        uint root = public_input[4];
        require(_roots[root], "merkletree root does not exist");
        require(!_nullifiers[sn_1], "sn_1 has existed, indicating this cm has been spent");
        require(!_nullifiers[sn_2], "sn_2 has existed, indicating this cm has been spent");
        bool re = openchannel_vf.verifyProof(a, b, c, public_input);
        require(re, "the verification of open_channel proof is not passed");
        _nullifiers[sn_1] = true;
        _nullifiers[sn_2] = true;
        // compute leaf_index of drcm
        uint drcm_leaf_index = merkletree.num_leaves();
        // insert drcm into merkletree
        merkletree.insert(drcm);
        // compute the root of merkle root
        uint256 drcm_merkle_root = merkletree.computeRoot(drcm_leaf_index);
        _roots[drcm_merkle_root] = true;
        // compute leaf_index of urcm
        uint urcm_leaf_index = merkletree.num_leaves();
        // insert drcm into merkletree
        merkletree.insert(urcm);
        // compute the root of merkle root
        uint256 urcm_merkle_root = merkletree.computeRoot(urcm_leaf_index);
        _roots[urcm_merkle_root] = true;
        return [drcm_leaf_index, urcm_leaf_index];
    }
    
    function close_channel(bytes32 message_hash, bytes memory signature, uint[2] memory a, uint[2][2] memory b, uint[2] memory c, uint[4] memory public_input, uint version_number) public returns(uint[2] memory){
        //ignore dispute period, assume anyone can immediately when requesting close channel
        //public_input: sn, new_urcm_r, new_urcm_s, root
        uint sn = public_input[0];
        uint new_urcm_r = public_input[1];
        uint new_urcm_s = public_input[2];
        uint root = public_input[3];
        require(_roots[root], "merkletree root does not exist");
        require(!_nullifiers[sn], "sn has existed, indicating this cm has been spent");
        //1. verify hash(message) == message_hash
        // bytes memory message = get_message(a,b,c,public_input,version_number);
        bytes32 message_hash_ = keccak256(get_message(a,b,c,public_input,version_number));
        require(message_hash == message_hash_, "message is not the same");
        //2. verify sign(message_hash) == signature
        address sender = signature_vf.verify_signature(message_hash, signature);
        require(msg.sender == sender, "the verification of signature is not passed");
        //3. verify proof
        bool re = offchaintransfer_vf.verifyProof(a,b,c,public_input);
        require(re, "the verification of offchain transfer proof is not passed");
        //4. after the above verification is finished, perform related operations
        _nullifiers[sn] = true;
        // compute leaf_index of drcm
        uint urcm_r_leaf_index = merkletree.num_leaves();
        // insert drcm into merkletree
        merkletree.insert(new_urcm_r);
        // compute the root of merkle root
        uint256 merkle_root_1 = merkletree.computeRoot(urcm_r_leaf_index);
        _roots[merkle_root_1] = true;
        // compute leaf_index of urcm
        uint urcm_s_leaf_index = merkletree.num_leaves();
        // insert drcm into merkletree
        merkletree.insert(new_urcm_s);
        // compute the root of merkle root
        uint256 merkle_root_2 = merkletree.computeRoot(urcm_s_leaf_index);
        _roots[merkle_root_2] = true;
        return [urcm_r_leaf_index, urcm_s_leaf_index];
    }
    
    function withdraw(address payable receive_address, uint[2] memory a, uint[2][2] memory b, uint[2] memory c, uint[3] memory public_input) public returns(bool){
        //public_input: sn, withdraw_value, root
        uint sn = public_input[0];
        uint root = public_input[1];
        uint withdraw_value = public_input[2];
        require(_roots[root], "merkletree root does not exist");
        require(!_nullifiers[sn], "sn has existed, indicating this cm has been spent");
        //verify proof
        bool re = withdraw_vf.verifyProof(a,b,c,public_input);
        require(re, "the verification of deposit proof is not passed");
        // after the above verification is finished, perform related operations
        _nullifiers[sn] = true;
        receive_address.transfer(withdraw_value);
        //if the contract is executed in here, indicating withdraw successfully
        bool withdraw_re = true;
        return withdraw_re;
    }
    
    function compute_merkle_path(uint leaf_index) public view returns(uint[DEPTH] memory){
        return merkletree.compute_merkle_path(leaf_index);
        
    } 
    
    //切片函数
  function get_message(uint[2] memory a, uint[2][2] memory b, uint[2] memory c, uint[4] memory public_input, uint version_number) public pure returns(bytes memory ){
      uint len = 13 * 32;
      bytes memory joined_message = new bytes(len);
      uint index = 0;
      bytes32 temp;
      for(uint i=0;i<2;i++){
          temp = bytes32(a[i]);
          for(uint j=0;j<32;j++){
              joined_message[index++]=temp[j];
          }
      }
      for(uint i=0;i<2;i++){
          for(uint j=0;j<2;j++){
              temp = bytes32(b[i][j]);
              for(uint k=0;k<32;k++){
                  joined_message[index++] = temp[k];
              }
          }
      }
      for(uint i=0;i<2;i++){
          temp = bytes32(c[i]);
          for(uint j=0;j<32;j++){
              joined_message[index++]=temp[j];
          }
      }
      for(uint i=0;i<4;i++){
          temp = bytes32(public_input[i]);
          for(uint j=0;j<32;j++){
              joined_message[index++]=temp[j];
          }
      }
      temp = bytes32(version_number);
          for(uint j=0;j<32;j++){
              joined_message[index++]=temp[j];
          }
      return joined_message;
  }
}
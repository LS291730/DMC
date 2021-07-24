// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.6.11;
contract SignatureVerifier{
  //公匙：0x60320b8a71bc314404ef7d194ad8cac0bee1e331
  //公钥是用来算出来后对比看看是否一直一致的
  
  //sha3(msg): 0x4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45 (web3.sha3("abc");)
  //这个是数据的哈希，验证签名时用到
  
  //签名后的数据：0xf4128988cbe7df8315440adde412a8955f7f5ff9a5468a791433727f82717a6753bd71882079522207060b681fbd3f5623ee7ed66e33fc8e581f442acbcf6ab800
  //签名后的数据，包含r,s，v三个内容
  
  //验证签名入口函数
  function verify_signature(bytes32 message_hash, bytes memory signedString) public pure returns (address){
    //   bytes32 message_hash = hex"4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45";
      //这是一个已经签名的数据
    //   bytes memory signedString =hex"f4128988cbe7df8315440adde412a8955f7f5ff9a5468a791433727f82717a6753bd71882079522207060b681fbd3f5623ee7ed66e33fc8e581f442acbcf6ab800";
    //   bytes memory signedString = hex"74f95e158f5f16e1db72c3e6b6429bbfce84a7ef328fbe1421bb5528da83038b0c756b8bb47bc71735b464a3fe38a2767fd7bb2591b17396853010f8c1383b3801";
      bytes32 r=bytesToBytes32(slice(signedString,0,32));
      bytes32 s=bytesToBytes32(slice(signedString,32,32));
      byte v = slice(signedString,64,1)[0];
      return ecrecoverDecode(message_hash, r,s,v);
      
  }
  
  //切片函数
  function slice(bytes memory data,uint start,uint len) public pure returns(bytes memory ){
      bytes memory b=new bytes(len);
      for(uint i=0;i<len;i++){
          b[i]=data[i+start];
      }
      return b;
  }

  //使用ecrecover恢复出公钥，后对比
  function ecrecoverDecode(bytes32 message_hash, bytes32 r,bytes32 s, byte v1) public pure returns(address addr){
      uint8 v=uint8(v1)+27;
      bytes memory prefix = "\x19Ethereum Signed Message:\n32";
      bytes32 prefixedHash = keccak256(abi.encodePacked(prefix, message_hash)); 
      addr=ecrecover(prefixedHash, v, r, s);
  }
  //bytes转换为bytes32
  function bytesToBytes32(bytes memory source) public pure returns(bytes32 result){
      assembly{
          result :=mload(add(source,32))
      }
  }
}


include "../../../../library/circomlib/circuits/mimc.circom"; //引入 mimc hash算法
include "../../../../library/circomlib/circuits/mimcsponge.circom"; //引入 mimc hash算法
include "../../../../library/circomlib/circuits/bitify.circom"; 
include "./get_merkle_root.circom"
template OffChainTransfer(){
    signal private input old_drcm;
    signal private input old_drnt[4]; //pk_s,pk_r,v,r
    signal private input new_urnt_r[3]; //pk_r,v1,r1
    signal private input new_urnt_s[3]; //pk_s,v2,r2
    signal private input path[5];
    signal private input sk_s;
    signal private input leaf_index;//the index of leaf

    signal output sn;
    signal output new_urcm_r;
    signal output new_urcm_s;
    signal output root;

    var depth = 5;

    //drcm = hash(pk_s,pk_r,v,r), urcm1 = hash(pk_r,v1,r1),urcm2=hash(pk_s,v2,r2)
    component hash[4];
    hash[0] = MiMCSponge(4,220,1); //drcm = hash(pk_s,pk_r,v,r)
    hash[0].ins[0] <== old_drnt[0];
    hash[0].ins[1] <== old_drnt[1];
    hash[0].ins[2] <== old_drnt[2];
    hash[0].ins[3] <== old_drnt[3];
    hash[0].k <== 0;
    old_drcm === hash[0].outs[0];

    hash[1] = MiMCSponge(3,220,1); //new_urcm_r = hash(pk_r,v1,r1)
    hash[1].ins[0] <== new_urnt_r[0];
    hash[1].ins[1] <== new_urnt_r[1];
    hash[1].ins[2] <== new_urnt_r[2];
    hash[1].k <== 0;
    new_urcm_r <== hash[1].outs[0];
    
    hash[2] = MiMCSponge(3,220,1); //new_urcm_s=hash(pk_s,v2,r2)
    hash[2].ins[0] <== new_urnt_s[0];
    hash[2].ins[1] <== new_urnt_s[1];
    hash[2].ins[2] <== new_urnt_s[2];
    hash[2].k <== 0;
    new_urcm_s <== hash[2].outs[0];
    
    hash[3] = MiMCSponge(2,220,1); //sn=hash(sk_s,r)
    hash[3].ins[0] <== sk_s;
    hash[3].ins[1] <== old_drnt[3];
    hash[3].k <== 0;
    sn <== hash[3].outs[0];
    
    old_drnt[2] === new_urnt_r[1] + new_urnt_s[1];

    component n2b = Num2Bits(depth);//get the bit of leaf index
    n2b.in <== leaf_index;
    component get_root = GetMerkleRoot(depth);
    get_root.leaf <== old_drcm;
    for(var j = 0; j < depth; j++){
        get_root.paths2_root[j] <== path[j];
        get_root.paths2_root_pos[j] <== n2b.out[j];
    }
    root <== get_root.out;
}
component main = OffChainTransfer();

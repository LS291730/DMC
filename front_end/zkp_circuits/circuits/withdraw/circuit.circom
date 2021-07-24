include "../../../../library/circomlib/circuits/mimc.circom"; //引入 mimc hash算法
include "../../../../library/circomlib/circuits/mimcsponge.circom"; //引入 mimc hash算法
include "../../../../library/circomlib/circuits/bitify.circom"; 
include "./get_merkle_root.circom"
template Withdraw(){
    signal private input urcm;
    signal private input pk;
    signal private input r;
    signal private input sk;
    signal private input leaf_index;
    signal private input path[5];

    signal input v;
    signal output sn;
    signal output root;

    var depth = 5;

    component hash[2];
    hash[0] = MiMCSponge(3,220,1); //urcm = hash(pk,v,r)
    hash[0].ins[0] <== pk;
    hash[0].ins[1] <== v;
    hash[0].ins[2] <== r;
    hash[0].k <== 0;
    urcm === hash[0].outs[0];

    hash[1] = MiMCSponge(2,220,1); //sn=hash(sk,r)
    hash[1].ins[0] <== sk;
    hash[1].ins[1] <== r;
    hash[1].k <== 0;
    sn <== hash[1].outs[0];

    component n2b = Num2Bits(depth);//get the bit of leaf index
    n2b.in <== leaf_index;
    component get_root = GetMerkleRoot(depth);
    get_root.leaf <== urcm;
    for(var j = 0; j < depth; j++){
        get_root.paths2_root[j] <== path[j];
        get_root.paths2_root_pos[j] <== n2b.out[j];
    }
    root <== get_root.out;
}

component main = Withdraw();

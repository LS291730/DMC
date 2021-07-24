include "../../../../circomlib/circuits/mimc.circom"; //引入 mimc hash算法
include "../../../../circomlib/circuits/mimcsponge.circom"; //引入 mimc hash算法
include "../../../../circomlib/circuits/bitify.circom"; 
include "./get_merkle_root.circom"
template OpenChannel(){
    signal private input old_urcm[2];
    signal private input old_note_1[3];//pk,v,r
    signal private input old_note_2[3];
    signal private input new_note_1[4];//s_pk,r_pk,v,r
    signal private input new_note_2[3];
    signal private input path_1[5];
    signal private input path_2[5];
    signal private input sk;//sender private key
    signal private input leaf_index[2];//the index of leaf

    signal output sn[2];//nullifier
    signal output drcm;
    signal output new_urcm;
    signal output root;
    signal computed_root[2];

    var depth = 5;

    //urcm = hash(pk,v,r), drcm = hash(s_pk,r_pk,v,r)
    component hash[6];
    hash[0] = MiMCSponge(3,220,1);//old_urcm[0] == hash(pk,v,r)
    hash[0].ins[0] <== old_note_1[0];
    hash[0].ins[1] <== old_note_1[1];
    hash[0].ins[2] <== old_note_1[2];
    hash[0].k <== 0;
    old_urcm[0] === hash[0].outs[0];

    hash[1] = MiMCSponge(3,220,1);//old_urcm[1] == hash(pk,v,r)
    hash[1].ins[0] <== old_note_2[0];
    hash[1].ins[1] <== old_note_2[1];
    hash[1].ins[2] <== old_note_2[2];
    hash[1].k <== 0;
    old_urcm[1] === hash[0].outs[0];

    hash[2] = MiMCSponge(4,220,1);//new_drcm == hash(s_pk,r_pk,v,r)
    hash[2].ins[0] <== new_note_1[0];
    hash[2].ins[1] <== new_note_1[1];
    hash[2].ins[2] <== new_note_1[2];
    hash[2].ins[3] <== new_note_1[3];
    hash[2].k <== 0;
    drcm <== hash[2].outs[0];

    hash[3] = MiMCSponge(3,220,1);//new_urcm == hash(pk,v,r)
    hash[3].ins[0] <== new_note_2[0];
    hash[3].ins[1] <== new_note_2[1];
    hash[3].ins[2] <== new_note_2[2];
    hash[3].k <== 0;
    new_urcm <== hash[3].outs[0];

    hash[4] = MiMCSponge(2,220,1);//sn == hash(sk,r)
    hash[4].ins[0] <== sk;
    hash[4].ins[1] <== old_note_1[2];
    hash[4].k <== 0;
    sn[0] <== hash[4].outs[0];

    hash[5] = MiMCSponge(2,220,1);//sn == hash(sk,r)
    hash[5].ins[0] <== sk;
    hash[5].ins[1] <== old_note_2[2];
    hash[5].k <== 0;
    sn[1] <== hash[5].outs[0];

    old_note_1[1] + old_note_2[1] === new_note_1[2] + new_note_2[1];

    component n2b[2];
    for(var i = 0; i < 2; i++){
        n2b[i] = Num2Bits(depth);//get the bit of leaf index
        n2b[i].in <== leaf_index[i];
    }

    component get_root[2]; 
    for(var i = 0; i < 2; i++){
        get_root[i] = GetMerkleRoot(depth);
        get_root[i].leaf <== old_urcm[i];
        for(var j = 0; j < depth; j++){
            get_root[i].paths2_root[j] <== path_1[j];
            get_root[i].paths2_root_pos[j] <== n2b[i].out[j];
        }
        computed_root[i] <== get_root[i].out;
    } 
    computed_root[0] === computed_root[1];
    out <== computed_root[0];
}
component main = OpenChannel();
include "../../../../library/circomlib/circuits/mimc.circom";
include "../../../../library/circomlib/circuits/mimcsponge.circom";
include "../../../../library/circomlib/circuits/eddsamimcsponge.circom";

template DepositProof(){
    signal private input public_key;
    signal private input random_r;
    signal input transfer_value;
    signal output urcm;
    
    component hash = MiMCSponge(3, 220, 1);
    hash.ins[0] <== public_key;
    hash.ins[1] <== transfer_value;
    hash.ins[2] <== random_r;
    hash.k <== 0;

    urcm <== hash.outs[0];
    


}

component main = DepositProof();

include "../../../../library/circomlib/circuits/mimc.circom"; //引入 mimc hash算法
template ComputeRoot(depth){
    signal input urcm;
    signal input path[depth];
    signal input index[depth];
    signal output out;

    var temp = urcm;
    component hash[depth];
    for(var i = 0; i < depth; i++){
        hash[i] = MiMC7(2);
        if(index[i] == 0){
            hash[i].x_in <== temp;
            hash[i].k <== path[i];
        }else{
            hash[i].x_in <== path[i];
            hash[i].k <== temp;
        }
        temp = hash[i].out;
    }
    out <== temp;
}   
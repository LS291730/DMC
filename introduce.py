'''
客户端功能
用户：发送方、接收方
5个步骤：存款、打开通道、转账、关闭通道、取款
存款：创建票据，用户界面接口Deposit(public_key, transfer_value)
    计算新票据：系统自动生成随机数r，urcm = commit(public_key, transfer_value, random_r)
    计算零知识证明：在linux系统中生成proof，其中public_input = (urcm, transfer_value), private_input = (public_key, random_r)
        groth16_prove(proving_key, circuit, input)==>proof.json + input.json
        groth16_verify(verfication_key, proof)==>true/false
    发布交易：向混币合约转账transfer_value个以太币/代币，交易data

打开通道：销毁旧票据，创建新票据，用户界面接口openChannel()
    选择两个旧票据old_note_i
    计算序列号(无效器)sn_i
    从混币合约中获得路径path_i
    计算两个新票据new_note_i
    计算零知识证明：其中public_input=(sn_1,sn_2,drcm,new_urcm,root),private_input=(old_urcm_i,old_note_pk,old_note_v_i,old_note_r_i,new_note_pk,new_note_v_1,new_note_r_1,new_note_v_2,new_note_r_2,sk,path_i)
        hash(old_note_pk,old_note_v_i,old_note_r_i)=old_urcm_i
        hash(old_note_pk,new_note_pk_1,new_note_v_1,new_note_r_1)=drcm
        hash(old_note_pk,new_note_v_2,new_note_r_2)=new_urcm
        hash(sk,old_note_r_i)=sn_i
        path_i from old_urcm_i is equal to root
        old_note_v_1 + old_note_v_2 = new_note_v_1 + new_note_v_2
    发布交易：向混币合约发送public_input and proof

链下转账：无需涉及智能合约，发送者利用支付通道(drcm票据看作发送者与接收者间的通道)，
        每次转账时即是对通道中代币进行重新分配。drcm——>urcm(recipient)+urcm(sender)
        计算drcm序列号(无效器)sn
        代币分配v=v1+v2
        计算两个新票据urcm_i
        从混币合约中获得drcm的路径path
        计算零知识证明：其中public_input=(sn,urcm_r,urcm_s,root), private_input=(drcm,pk_s,pk_r,v,v1,v2,sk_s,path,r1,r2)
            drcm=hash(pk_s,pk_r,v,r)
            sn=hash(sk_s,r ) //需要验证nullifier[sn]=false，若为true，则已花费。
            a path from drcm to root
            urcm_r=hash(pk_r,v1,r1) //需要证明drcm中的pk_r和urcm中的pk_r相同
            urcm_s=hash(pk_s,v2,r2) );
            v=v1+v2
        由零知识证明得到offchainproof=(proof,public_input)，version number=w
        message=(offchainproof,w),发送者对message进行签名得δ，将(message,δ)发送给接收者

关闭通道：发送者和接收者都可以申请关闭，即将双方间最后交易提交到区块链上，
        混币合约销毁drcm，插入2个urcm
        发送者/接收者：与混币合约中closechannel函数交互，输入(message,signature),
                    message=(offchainproof,version_number),
                    offchainproof=(proof+public_input:sn,new_urcm_r,new_urcm_s,root)
                    收到合约返回的urcm_leaf_index，应该把对应的叶子下标发送给另一方
        混币合约：争议期
                假设发送者向合约申请关闭通道，合约等待Δ时间，期间，若接收者发现发送者不诚实，则向合约发送最新版本号的交易
                取最高版本号的交易，验证交易，验证零知识证明drcm存在且未被花费，新插入的urcm形式正确
问题一：争议期中发送争议时，接收者向混币合约提交最新nonce交易，可能会泄露发送者和接收者间交易关系；
问题二：接收者如何得知发送者向合约提交关闭通道请求——钱包端监测发送者向合约发送的交易，若是关闭与接收者间的通道，就通知接收者
只需一轮争议期，因为：
    若接收者申请关闭通道，则无需争议期，因为不论接收者是否发送最新版本号，都不会损害发送者利益。
    若发送者申请关闭通道，发送了非最新版本号的交易，接收者发送更高版本号进行反驳后，发送者无需再进行反驳。
问题：好像无法区分发送者和接收者，所以就不区分发送者和接收者，一律需要一轮争议期 


取款：与存款对应，销毁票据，用户界面接口withdraw(receive_account)
    用户：选择待销毁的票据及其再混币合约merkle树中的下标leaf_index，urcm=hash(pk,v,r)
        计算无效器，sn=hash(sk,r)
        从混币合约中获得urcm到root的路径path
        生成零知识证明，public_input=(sn,v,root),private_input=(urcm,pk,sk,r,leaf_index,path)
            urcm=hash(pk,v,r)
            sn=hash(sk,r)
            a path from urcm to root
    混币合约：存储sn，向receive_account转账v个eth
'''
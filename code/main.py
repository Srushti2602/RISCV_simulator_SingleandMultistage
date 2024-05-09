import os
import argparse
from copy import deepcopy

MemSize = 1000 # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.

class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        # self.case = case

        with open(os.path.join(ioDir ,"imem.txt")) as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress):
        #read instruction memory
        #return 32 bit hex val
        instruction = ""
        for i in range(ReadAddress,ReadAddress+4):
            instruction = instruction + self.IMem[i]
        return instruction

          
class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        # self.case = case
        with open(os.path.join(ioDir , "dmem.txt")) as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]
            self.DMem = (self.DMem + 1000*['00000000'])[:1000]

    def readInstr(self, ReadAddress):
        #read data memory
        #return 32 bit hex val
        data = ""
        for i in range(ReadAddress,ReadAddress+4):
            data = data + self.DMem[i]
        return data
            
    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
        parsedData = [WriteData[:8], WriteData[8:16], WriteData[16:24], WriteData[24:]]
        for i in range(4):
            self.DMem[Address+i] = parsedData[i]

                     
    def outputDataMem(self):
        print(self.ioDir)
        resPath = os.path.join(self.ioDir ,  self.id + "_DMEMResult.txt") 
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])

class RegisterFile(object):
    def __init__(self, ioDir, dmem, id):

        # case = dmem.case
        self.id = id
        self.outputFile = os.path.join(ioDir, self.id + "_RFResult.txt")
        self.Registers = ['00000000000000000000000000000000' for i in range(32)]
    
    def readRF(self, Reg_addr):
        # Fill in
        return self.Registers[Reg_addr]
    
    def writeRF(self, Reg_addr, Wrt_reg_data):
        # Fill in
        self.Registers[Reg_addr]=Wrt_reg_data
        pass
         
    def outputRF(self, cycle):
        op = ["State of RF after executing cycle:   " + str(cycle) + "\n"]
        op.extend([str(val)+"\n" for val in self.Registers])
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0,"jump_link": 0}
        self.ID = {"nop": False, "Instr": 0, "Forwarding1": 0, "Forwarding2": 0, "branch": 0}
        self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0, 
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0, "opcode": 0, "funct3": 0, "funct7": 0, "LW_hazard_stall": 0, "LW_hazard_stall_cycle": -10}
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0, 
                   "wrt_mem": 0, "wrt_enable": 0, "halted": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0, "halted": 0}

class Core(object):
    def __init__(self, ioDir, imem, dmem, id):
        self.myRF = RegisterFile(ioDir, dmem, id)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem

    def bin_to_dec(self ,binary, dig):
        while len(binary)<dig :
                binary = '0'+binary
        if binary[0] == '0':
                return int(binary, 2)
        else:
                return -1 * (int(''.join('1' if x == '0' else '0' for x in binary), 2) + 1)

    def dec_to_bin(self, decimal, dig):
        if decimal>=0:
            temp = bin(decimal).split("0b")[1]
            while len(temp)<dig :
                temp = '0'+temp
            return temp
        else:
            temp = -1*decimal
            return bin(temp-pow(2,dig)).split("0b")[1]




class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem, id):
        super(SingleStageCore, self).__init__(ioDir, imem, dmem, id)
        self.opFilePath = os.path.join(ioDir ,"StateResult_SS.txt")

        # case = dmem.case

        new_path = os.path.join(ioDir) 

        if not os.path.exists(new_path): 
            os.mkdir(new_path)

        new_path = os.path.join(new_path ) 
        if not os.path.exists(new_path): 
            os.mkdir(new_path)

        self.opFilePath = os.path.join(ioDir , 'StateResult_SS.txt')

        
    def step(self):
        # Your implementation
        instruction=imem.readInstr(self.state.IF["PC"])
        self.nextState.IF["PC"]=self.state.IF["PC"]+4

        # ID
        self.state.ID["Instr"]=instruction
        self.state.EX["Rs"]=int(instruction[-20:-15],2)
        self.state.EX["Read_data1"]=self.bin_to_dec(str(self.myRF.readRF(self.state.EX["Rs"])),32)
        self.state.EX["Rt"]=int(instruction[-25:-20],2)
        self.state.EX["Read_data2"]=self.bin_to_dec(str(self.myRF.readRF(self.state.EX["Rt"])),32)
        self.state.EX["Wrt_reg_addr"]=int(instruction[-12:-7],2)
        funct3=instruction[-15:-12]
        funct7=instruction[-32:-25]
        immIL=self.bin_to_dec(instruction[-32:-20],12)
        immS=self.bin_to_dec(instruction[-32:-25]+instruction[-12:-7],12)
        immJ=self.bin_to_dec(instruction[-32]+instruction[-20:-12]+instruction[-21]+instruction[-31:-21]+'0',21)
        immB=self.bin_to_dec(instruction[-32]+instruction[-8]+instruction[-31:-25]+instruction[-12:-8]+'0',13)
        opcode=instruction[-7:]
        imm=0

        # EX
        self.state.MEM["Rs"] = self.state.EX["Rs"]
        self.state.MEM["Rt"] = self.state.EX["Rt"]
        self.state.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
        # R type instruction
        if opcode == '0110011':
            self.state.EX["is_I_type"]=False
            # Subtract
            if funct7 == '0100000':
                self.state.MEM["ALUresult"]=self.state.EX["Read_data1"] - self.state.EX["Read_data2"]
                print("sub")
            elif funct7 == '0000000':
                # Add
                if funct3 == '000':
                    print("Add")
                    self.state.MEM["ALUresult"]=self.state.EX["Read_data1"] + self.state.EX["Read_data2"]
                # XOR
                elif funct3 == '100':
                    print("xor")
                    self.state.MEM["ALUresult"]=self.state.EX["Read_data1"] ^ self.state.EX["Read_data2"]
                # OR
                elif funct3 == '110':
                    print("or")
                    self.state.MEM["ALUresult"]=self.state.EX["Read_data1"] | self.state.EX["Read_data2"]
                # AND
                elif funct3 == '111':
                    print("and")
                    self.state.MEM["ALUresult"]=self.state.EX["Read_data1"] & self.state.EX["Read_data2"]

        # I-type instructions
        elif opcode == '0010011':
            self.state.EX["is_I_type"]=True
            imm=immIL
            # Addi
            if funct3 == '000':
                print('addi')
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] + immIL
            # xori
            elif funct3 == '100':
                print('xori')
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] ^ immIL
            # ori
            elif funct3 == '110':
                print('ori')
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] | immIL
            # andi
            elif funct3 == '111':
                print('andi')
                self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] & immIL

        # J-type instruction
        elif opcode == '1101111':
            print('jump')
            imm=immJ
            self.state.MEM["ALUresult"] = self.nextState.IF["PC"]
            self.nextState.IF["PC"] = self.nextState.IF["PC"] - 4 + immJ

        # B-type instruction
        elif opcode == "1100011":
            imm=immB
            # BEQ
            if funct3 == '000':
                print('beq')
                self.nextState.IF["PC"] = self.nextState.IF["PC"] - 4 + immB if self.state.EX["Read_data1"]-self.state.EX["Read_data2"] == 0 else self.nextState.IF["PC"]
            # BNE
            elif funct3 == '001':
                print('bne')
                self.nextState.IF["PC"] = self.nextState.IF["PC"] - 4 + immB if self.state.EX["Read_data1"]-self.state.EX["Read_data2"] != 0 else self.nextState.IF["PC"]

        # LW
        elif opcode == "0000011":
            imm=immIL
            print('lw')
            self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] + immIL
            self.state.EX["rd_mem"] = 1

        # SW
        elif opcode == "0100011":
            imm=immS
            print('sw')
            self.state.MEM["ALUresult"] = self.state.EX["Read_data1"] + immS
            self.state.EX["wrt_mem"] = 1
            
        elif opcode == "1111111":
            print('halted')
            self.nextState.IF["nop"]=True
            self.nextState.IF["PC"]=self.state.IF["PC"]
        print('{}\tPC:{}:\tX{}\tX{}\tX{}\t{}'.format(self.cycle,self.nextState.IF["PC"], self.state.EX["Wrt_reg_addr"], self.state.EX["Rs"], self.state.EX["Rt"], imm))


        # MEM + WB
        # SW
        if self.state.EX["wrt_mem"]:
            data_wrt=str(self.dec_to_bin(self.state.EX["Read_data2"],32))
            dmem_ss.writeDataMem(self.state.MEM["ALUresult"], data_wrt)

        # LW
        if self.state.EX["rd_mem"]:
            self.myRF.writeRF(self.state.EX["Wrt_reg_addr"], dmem_ss.readInstr(self.state.MEM["ALUresult"]))

        # WB for all other instructions
        if ((not(self.state.EX["rd_mem"])) and (not (self.state.EX["wrt_mem"])) and (opcode != '1100011') and (self.state.EX["Wrt_reg_addr"]!=0)):
            self.myRF.writeRF(self.state.EX["Wrt_reg_addr"], self.dec_to_bin(self.state.MEM["ALUresult"],32))

        self.nextState.EX["rd_mem"] = 0
        self.nextState.EX["wrt_mem"] = 0
        self.nextState.EX["is_I_type"] = False
        


        if self.state.IF["nop"]:
            self.halted = True
            
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        self.state=deepcopy(self.nextState) #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1
        print('end of cycle\n')

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        
        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem, id):
        super(FiveStageCore, self).__init__(ioDir , imem, dmem, id)

        self.opFilePath = os.path.join(ioDir ,   "StateResult_FS.txt")

    def step(self):
        # Your implementation
        # --------------------- WB stage --------------------- JAL Implementation not done
        print('\n*********CYCLE {}********PC: {}*******'.format(self.cycle, self.state.IF["PC"]))
        if not self.state.WB["nop"]  and self.cycle>=4:
            print("WB:", self.cycle, 'Register:', self.state.WB["Wrt_reg_addr"], 'Data:', self.state.WB["Wrt_data"])
            if self.state.WB["wrt_enable"]:
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"],self.state.WB["Wrt_data"])
        elif self.cycle>=4:
            self.state.MEM["nop"] = True

        
        # --------------------- MEM stage --------------------
        if not self.state.MEM["nop"] and self.cycle>=3:
            if self.state.MEM["wrt_mem"]:
                if (type(self.state.MEM["Store_data"])==int):
                    data=str(self.dec_to_bin(self.state.MEM["Store_data"],32))
                else:
                    data=self.state.MEM["Store_data"]
                dmem_fs.writeDataMem(self.state.MEM["ALUresult"], data)
                print("MEM: SW Cycle:", self.cycle, 'Address:', self.state.MEM["ALUresult"], 'Data:', data)
            self.nextState.WB["wrt_enable"] = self.state.MEM["wrt_enable"]
            if self.state.MEM["wrt_enable"] and self.state.MEM["Wrt_reg_addr"]!=0:
                if self.state.MEM["rd_mem"]:
                    self.nextState.WB["Wrt_data"] = dmem_fs.readInstr(self.state.MEM["ALUresult"])
                else:
                    self.nextState.WB["Wrt_data"] = str(self.dec_to_bin(self.state.MEM["ALUresult"],32))
                self.nextState.WB["Rs"] = self.state.MEM["Rs"]
                self.nextState.WB["Rt"] = self.state.MEM["Rt"]
                self.nextState.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
            print('MEM: {}\t\tX{}\tX{}\tX{}\tRM:{}\tWM:{}\tWE:{}'.format(self.cycle,self.state.MEM["Wrt_reg_addr"],self.state.MEM["Rs"],self.state.MEM["Rt"],self.state.MEM["rd_mem"],self.state.MEM["wrt_mem"],self.state.MEM["wrt_enable"]))

        elif self.cycle>=3:
            self.state.EX["nop"] = True
            if self.state.MEM["halted"] == 1:
                self.state.WB["nop"] = True
                            
                
        
        # --------------------- EX stage ---------------------
        if self.state.EX["LW_hazard_stall"]:
            print("stall")
            self.nextState.EX["LW_hazard_stall"]=False
            self.nextState.EX["nop"]=False
            self.nextState.ID["nop"]=False
            self.nextState.IF["nop"]=False
        elif not self.state.EX["nop"] and self.cycle>=2:
            opcode=self.state.EX["opcode"]
            funct3=self.state.EX["funct3"]
            funct7=self.state.EX["funct7"]
            imm=self.state.EX["Imm"]
            self.nextState.MEM["Rs"] = self.state.EX["Rs"]
            self.nextState.MEM["Rt"] = self.state.EX["Rt"]
            self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
            self.nextState.MEM["rd_mem"] = self.state.EX["rd_mem"]
            self.nextState.MEM["wrt_mem"] = self.state.EX["wrt_mem"]
            self.nextState.MEM["wrt_enable"] = 0
            inst=""
            if (self.state.EX["Read_data1"]!=0 and type(self.state.EX["Read_data1"])!=int):
                self.state.EX["Read_data1"]=self.bin_to_dec(self.state.EX["Read_data1"],32)
            if (self.state.EX["Read_data2"]!=0 and type(self.state.EX["Read_data2"])!=int):
                self.state.EX["Read_data2"]=self.bin_to_dec(self.state.EX["Read_data2"],32)
            print('Data in EX Registers:    Data1 :', self.state.EX["Read_data1"],'Data 2:', self.state.EX["Read_data2"])

            # R type instruction
            if opcode == '0110011':
                self.nextState.MEM["wrt_enable"] = self.state.EX["wrt_enable"]
                self.state.EX["is_I_type"]=False
                # Subtract
                if funct7 == '0100000':
                    self.nextState.MEM["ALUresult"]=self.state.EX["Read_data1"] - self.state.EX["Read_data2"]
                    inst="Sub"
                elif funct7 == '0000000':
                    # Add
                    if funct3 == '000':
                        inst="Add"
                        self.nextState.MEM["ALUresult"]=self.state.EX["Read_data1"] + self.state.EX["Read_data2"]
                    # XOR
                    elif funct3 == '100':
                        inst="XOR"
                        self.nextState.MEM["ALUresult"]=self.state.EX["Read_data1"] ^ self.state.EX["Read_data2"]
                    # OR
                    elif funct3 == '110':
                        inst="OR"
                        self.nextState.MEM["ALUresult"]=self.state.EX["Read_data1"] | self.state.EX["Read_data2"]
                    # AND
                    elif funct3 == '111':
                        inst="AND"
                        self.nextState.MEM["ALUresult"]=self.state.EX["Read_data1"] & self.state.EX["Read_data2"]
            # I-type instructions
            elif opcode == '0010011':
                self.state.EX["is_I_type"]=True
                self.nextState.MEM["wrt_enable"] = self.state.EX["wrt_enable"]
                # Addi
                if funct3 == '000':
                    inst="ADDI"
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] + imm
                # xori
                elif funct3 == '100':
                    inst="XORI"
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] ^ imm
                # ori
                elif funct3 == '110':
                    inst="ORI"
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] | imm
                # andi
                elif funct3 == '111':
                    self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] & imm
                    inst="ANDI"

            # J-type instruction
            elif opcode == '1101111':
                inst="JUMP"
                self.nextState.MEM["wrt_enable"] = self.state.EX["wrt_enable"]
                self.nextState.MEM["ALUresult"] = self.state.IF["jump_link"]

            # B-type instruction
            elif opcode == "1100011":

                # BEQ
                if funct3 == '000':
                    inst="BEQ"
                    # self.nextState.IF["PC"] = self.state.IF["PC"] + imm if self.state.EX["Read_data1"]-self.state.EX["Read_data2"] == 0 else self.state.IF["PC"]
                # BNE
                elif funct3 == '001':
                    inst="BNE"
                    # self.nextState.IF["PC"] = self.state.IF["PC"] + imm if self.state.EX["Read_data1"]-self.state.EX["Read_data2"] != 0 else self.state.IF["PC"]

            # LW
            elif opcode == "0000011":
                inst="LW"
                self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] + imm
                self.nextState.MEM["wrt_enable"] = self.state.EX["wrt_enable"]

            # SW
            elif opcode == "0100011":
                inst="SW"
                self.nextState.MEM["ALUresult"] = self.state.EX["Read_data1"] + imm
                self.nextState.MEM["Store_data"] = self.state.EX["Read_data2"]
                
            elif opcode == "1111111":
                inst="HALTED"
                self.nextState.MEM["nop"]=True
                self.nextState.MEM["halted"]=1


            print('EX: {}\t{}\tX{}\tX{}\tX{}\t{}'.format(self.cycle, inst,self.state.EX["Wrt_reg_addr"], self.state.EX["Rs"],self.state.EX["Rt"],self.state.EX["Imm"]))
            
        elif self.cycle>=2:
            self.state.ID["nop"] = True

    
    
        # --------------------- ID stage ---------------------
        self.nextState.IF["jump_link"]=self.state.IF["jump_link"]
        if not self.state.ID["nop"] and self.cycle>=1:
            instruction = self.state.ID["Instr"]
            self.nextState.EX["Rs"]=int(instruction[-20:-15],2)
            self.nextState.EX["Rt"]=int(instruction[-25:-20],2)
            self.nextState.EX["Wrt_reg_addr"]=int(instruction[-12:-7],2)
            opcode=instruction[-7:]
            funct3=instruction[-15:-12]
            funct7=instruction[-32:-25]
            self.nextState.EX["opcode"]=opcode
            self.nextState.EX["funct3"]=funct3
            self.nextState.EX["funct7"]=funct7
            immIL=self.bin_to_dec(instruction[-32:-20],12)
            immS=self.bin_to_dec(instruction[-32:-25]+instruction[-12:-7],12)
            immJ=self.bin_to_dec(instruction[-32]+instruction[-20:-12]+instruction[-21]+instruction[-31:-21]+'0',21)
            immB=self.bin_to_dec(instruction[-32]+instruction[-8]+instruction[-31:-25]+instruction[-12:-8]+'0',13)
            self.nextState.EX["wrt_enable"]=1
            self.nextState.EX["wrt_mem"]=0
            self.nextState.EX["rd_mem"]=0
            imm=0
            match opcode:
                case '0010011':
                    imm=immIL
                case '0000011':
                    imm=immIL
                    self.nextState.EX["rd_mem"]=1
                case '0100011':
                    imm=immS
                    self.nextState.EX["wrt_mem"]=1
                    self.nextState.EX["wrt_enable"]=0
                case '1101111':
                    imm=immJ
                case '1100011':
                    imm=immB
                    self.nextState.EX["wrt_enable"]=0
                case _:
                    imm=0
            self.nextState.EX["Imm"] = imm
            if (self.state.EX["rd_mem"]):
                if ((self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rs"] or self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rt"]) and self.nextState.MEM["wrt_enable"] and self.nextState.MEM["Wrt_reg_addr"]!=0):
                    self.nextState.EX["LW_hazard_stall"]=True
                    print('LWHAZARD')
                    self.state.ID["Forwarding1"]=1
                    self.state.ID["Forwarding2"]=1
                    self.state.IF["nop"]=True
                elif ((self.nextState.WB["Wrt_reg_addr"]==self.nextState.EX["Rs"]) and self.nextState.WB["wrt_enable"] and self.nextState.WB["Wrt_reg_addr"]!=0):
                    self.nextState.EX["Read_data1"]=self.nextState.WB["Wrt_data"]
                    self.state.ID["Forwarding1"]=1
                    print('LWHAZARD-2')
                elif ((self.nextState.WB["Wrt_reg_addr"]==self.nextState.EX["Rt"]) and self.nextState.WB["wrt_enable"] and self.nextState.WB["Wrt_reg_addr"]!=0):
                    self.nextState.EX["Read_data2"]=self.nextState.WB["Wrt_data"]
                    self.state.ID["Forwarding2"]=1
                    print('LWHAZARD-3')
            if (self.nextState.EX["wrt_mem"] and not self.state.MEM["wrt_mem"]):
                if (self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rs"] and self.nextState.MEM["Wrt_reg_addr"]!=0):
                    self.nextState.EX["Read_data1"] = self.nextState.MEM["ALUresult"]
                    print("SWHAZARD-1")
                    self.state.ID["Forwarding1"]=1
            if (self.nextState.MEM["wrt_mem"] and not self.state.MEM["wrt_mem"]):
                if (self.nextState.WB["Wrt_reg_addr"]==self.nextState.MEM["Rt"] and self.nextState.WB["Wrt_reg_addr"]!=0):
                    self.nextState.MEM["Store_data"] = self.nextState.WB["Wrt_data"]
                    print("SWHAZARD-2")
                    self.state.ID["Forwarding2"]=1
            if (self.nextState.MEM["wrt_mem"]):
                if (self.state.WB["Wrt_reg_addr"]==self.nextState.MEM["Rt"] and self.nextState.WB["Wrt_reg_addr"]!=0):
                    self.nextState.MEM["Store_data"] = self.state.WB["Wrt_data"]
                    print("SWHAZARD-3")
            if (self.nextState.WB["Wrt_reg_addr"]==self.nextState.EX["Rs"] and self.nextState.WB["wrt_enable"] and self.nextState.WB["Wrt_reg_addr"]!=0):
                    print('ID/EX-MEM/WB-RS1')
                    self.nextState.EX["Read_data1"] = self.nextState.WB["Wrt_data"]
                    self.state.ID["Forwarding1"]=1
            if (self.nextState.WB["Wrt_reg_addr"]==self.nextState.EX["Rt"] and self.nextState.WB["wrt_enable"] and self.nextState.WB["Wrt_reg_addr"]!=0):
                    if not (self.nextState.EX["wrt_mem"]):
                        print('ID/EX-MEM/WB-RS2')
                        self.nextState.EX["Read_data2"] = self.nextState.WB["Wrt_data"]
                        self.state.ID["Forwarding2"]=1
            if (self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rs"] and self.nextState.MEM["wrt_enable"] and self.nextState.MEM["Wrt_reg_addr"]!=0):
                    if not (self.nextState.MEM["rd_mem"]):
                        self.nextState.EX["Read_data1"] = self.nextState.MEM["ALUresult"]
                        print('ID/EX-EX/MEM-RS1')
                        self.state.ID["Forwarding1"]=1
            if (self.nextState.MEM["Wrt_reg_addr"]==self.nextState.EX["Rt"] and self.nextState.MEM["wrt_enable"] and self.nextState.MEM["Wrt_reg_addr"]!=0):
                    if not (self.nextState.MEM["rd_mem"] or self.nextState.EX["wrt_mem"]):
                        print('ID/EX-EX/MEM-RS2')
                        self.nextState.EX["Read_data2"] = self.nextState.MEM["ALUresult"]
                        self.state.ID["Forwarding2"]=1
            if (self.state.ID["Forwarding1"]!=1):
                self.nextState.EX["Read_data1"]=self.bin_to_dec(self.myRF.readRF(self.nextState.EX["Rs"]),32)
            if (self.state.ID["Forwarding2"]!=1):
                self.nextState.EX["Read_data2"]=self.bin_to_dec(self.myRF.readRF(self.nextState.EX["Rt"]),32)
            if (self.nextState.EX["Read_data1"]!=0 and type(self.nextState.EX["Read_data1"])!=int):
                self.nextState.EX["Read_data1"]=self.bin_to_dec(self.nextState.EX["Read_data1"],32)
            if (self.nextState.EX["Read_data2"]!=0 and type(self.nextState.EX["Read_data2"])!=int):
                self.nextState.EX["Read_data2"]=self.bin_to_dec(self.nextState.EX["Read_data2"],32)
            if (opcode=='1100011'):
                if funct3 == '000':
                    print("BEQ-ID")
                    if (self.nextState.EX["Read_data1"]==self.nextState.EX["Read_data2"]):
                        self.state.IF["nop"]=True
                        self.nextState.ID["nop"]=True
                        self.nextState.ID["branch"]=1
                        self.nextState.IF["PC"]=self.state.IF["PC"]+imm-4
                        print("Branch Taken")
                    else:
                        print("Branch not taken")
                if funct3 == '001':
                    print("BNE-ID")
                    if (self.nextState.EX["Read_data1"]!=self.nextState.EX["Read_data2"]):
                        self.state.IF["nop"]=True
                        self.nextState.ID["nop"]=True
                        self.nextState.ID["branch"]=1
                        self.nextState.IF["PC"]=self.state.IF["PC"]+imm-4
                        print("Branch Taken")
                    else:
                        print("Branch not taken")
            self.state.ID["Forwarding1"]=0
            self.state.ID["Forwarding2"]=0
            if instruction == "11111111111111111111111111111111":
                self.state.IF["nop"]=True
                self.nextState.ID["nop"]=True
            print('ID: {}\t\tX{}\tX{}\tX{}\t{}'.format(self.cycle, self.nextState.EX["Wrt_reg_addr"], self.nextState.EX["Rs"], self.nextState.EX["Rt"], imm))
        elif self.cycle>=1:
            if (self.state.ID["branch"]==1):
                self.nextState.IF["nop"]=False
                self.nextState.ID["branch"]=0
                self.nextState.ID["nop"]=False
            else:
                self.state.IF["nop"] = True

        
        # --------------------- IF stage ---------------------
        if not self.state.IF["nop"]:
            instruction=imem.readInstr(self.state.IF["PC"])
            self.nextState.ID["Instr"] = instruction
            if (instruction[-7:]=='1101111'):
                self.nextState.IF["jump_link"]=self.state.IF["PC"]+4
                self.nextState.IF["PC"]=self.state.IF["PC"]+self.bin_to_dec(instruction[-32]+instruction[-20:-12]+instruction[-21]+instruction[-31:-21]+'0',21)
            else:
                self.nextState.IF["PC"]+=4
            print('IF: {}'.format(self.cycle))

        #self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True
        print('*END OF CYCLE****PC:{}****NEXT PC:{}*****'.format(self.state.IF["PC"], self.nextState.IF["PC"]))
        self.myRF.outputRF(self.cycle) # dump RF
        self.printState(self.nextState, self.cycle) # print states after executing cycle 0, cycle 1, cycle 2 ... 
        self.state=deepcopy(self.nextState) #The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-"*70+"\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if(cycle == 0): perm = "w"
        else: perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

if __name__ == "__main__":
     
    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    ioPar = os.path.dirname(ioDir)
    print("IO Directory:", ioDir)

        
    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem(name="SS", ioDir=ioDir)
    dmem_fs = DataMem(name="FS", ioDir=ioDir)
    
    ssCore = SingleStageCore(ioDir, imem, dmem_ss, "SS")
    fsCore = FiveStageCore(ioDir, imem, dmem_fs, "FS")

    while(True):
        if not ssCore.halted:
            ssCore.step()
        
        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break
    
        # dump SS and FS data mem.
        dmem_ss.outputDataMem()
        dmem_fs.outputDataMem()

        num_ins=len(imem.IMem)/4

        data = '''Single stage implementation:
                Number of cycles: {}
                Number of instructions executed: {}
                Average CPI: {}
                Instructions per cycle: {}
                '''.format(ssCore.cycle, num_ins, ssCore.cycle/num_ins, num_ins/ssCore.cycle)
        
        data_fs = '''Five Stage Pipelined implementation:
                Number of cycles: {}
                Number of instructions executed: {}
                Average CPI: {}
                Instructions per cycle: {}
                '''.format(fsCore.cycle, num_ins, fsCore.cycle/num_ins, num_ins/fsCore.cycle)
        
        with open(os.path.join( ioDir,"PerformanceMetrics_SS_Result.txt"), "w") as rp:
            rp.writelines(data)

        with open(os.path.join( ioDir, "PerformanceMetrics_FS_Result.txt"), "w") as rp:
            rp.writelines(data_fs)

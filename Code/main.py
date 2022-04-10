from machine import Pin
import time


# Set here the input clock, I'm using a board with a 20MHz oscillator
# Set to 10MHz if connected to the atomic clock 
SYSCLK = 60E6;
# Set clock multiplier (that will determine the frequency precision)
# Max output freq is 1/2 F * (MULT * CLK)
# The AD9854 has an internal PLL 
CLKMULT = 4;

# Addresses for F1 & F2
addrF1 = 4;
addrF2 = 10;
addrDelta = 16;



# Define the GPIO pins
mreset = Pin(16, Pin.OUT) 
osk = Pin(15, Pin.OUT) 
pmode = Pin(17, Pin.OUT) 
rdb = Pin(14, Pin.OUT) 
wrb = Pin(18, Pin.OUT) 
ioud = Pin(13, Pin.OUT)
fsk = Pin(2, Pin.OUT)
a0 = Pin(19, Pin.OUT) 
a1 = Pin(12, Pin.OUT) 
a2 = Pin(20, Pin.OUT) 
a3 = Pin(11, Pin.OUT) 
a4 = Pin(21, Pin.OUT) 
a5 = Pin(10, Pin.OUT) 
d0 = Pin(22, Pin.OUT) 
d1 = Pin(9, Pin.OUT) 
d2 = Pin(8, Pin.OUT) 
d3 = Pin(7, Pin.OUT) 
d4 = Pin(6, Pin.OUT) 
d5 = Pin(5, Pin.OUT)
d6 = Pin(4, Pin.OUT)
d7 = Pin(3, Pin.OUT)

trigger = Pin(0, Pin.OUT)

led = Pin(25, Pin.OUT)


addresses = [a5, a4, a3, a2, a1, a0]
datas = [d7, d6, d5, d4, d3, d2, d1, d0]
masks = [int('10000000', 2), int('01000000', 2), int('00100000', 2), int('00010000', 2), int('00001000', 2), int('00000100', 2), int('00000010', 2), int('00000001', 2)]
masks2 = [int('00100000', 2), int('00010000', 2), int('00001000', 2), int('00000100', 2), int('00000010', 2), int('00000001', 2)]

def WR_D_A(addr, data):
    # Write data to address
    for i,a in enumerate(addresses) :
        a.on() if addr & masks[i+2] == masks[i+2] else a.off()
        #print("a",i,": on") if addr & masks[i] == masks[i] else print("a",i, ": off")

    # Write data to data
    for j,d in enumerate(datas) :
        d.on() if data & masks[j] == masks[j] else d.off()
        #print("d",i,": on") if data & masks[i] == masks[i] else print("d",i, ": off")
    wrb.off()
    wrb.on()
    
    #print(addr&int('11111111', 2), " : ",data&int('11111111', 2))

# Clocks the external update clock 
# this works if pin 20 is set to 0 when writing the registers
# otherwise the internal clock has to be used an synchronized to the raspberry
def Update_CLK():
    ioud.on()
    ioud.off()

def Init_AD9854(mode):
    # Set device in parallel mode
    pmode.on()
    # Set the WRB pin to high
    wrb.on()
    # Set the RDB pin to high
    rdb.on()
    # Set the I/O UD pin to low
    ioud.off()
    # Set the MRESET pin to high
    mreset.on()
    # Set the MRESET pin to low
    mreset.off()
    # No mode should be powered off
    # No power saving
    WR_D_A(0x1d, 0x00)
    WR_D_A(0x1e, CLKMULT)
    #Set sysmode to 0x00 (no internal update clock!)
    WR_D_A(0x1f, mode)
    #OSK EN, Keep sinc filter enabled
    #WR_D_A(0x20, 0x60)
    #OSK EN, disable sinc filter (300mA less current needed)
    WR_D_A(0x20, 0x20)
    Update_CLK()


# Resets accumulators :
# N = 2 Resets ACC 1 (10)
# N = 1 Resets ACC 2 (01)
# N = 3 Resets ACC 1 & 2 (11)
def Rst_ACC(N,mode):
    # Assuming this happens always after a init this is not needed
    #WR_D_A(0x1f, (0x00)+mode)
    WR_D_A(0x1f, (N<<6)+mode)
    WR_D_A(0x1f, mode)
    Update_CLK()

# Calculates the 2-complement of a int
def twos_comp(val, bits):
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val                         # return positive value as is


# Set_frequency sets frequency and amplitude
# Frequency (max CLK/2)
# Amplitude (max 4096)
def Set_freq(freq,ampl,N):
    # FTW for calculating the bit frequency
    FTW = round((freq*(2**48))/(SYSCLK*CLKMULT));
    # Set frequency addresses [4,9] to FTW
    for i in range(6):
        WR_D_A(N+i,FTW>>(40-8*i)) 
    # Set I channel ampl addresses 0x[21,22] to amlitude
    if ampl > 0 :
        WR_D_A(0x21, ampl>>8 )
        WR_D_A(0x22, ampl)
        # Set Q channel ampl addresses 0x[21,22] to amlitude
        WR_D_A(0x23, ampl>>8 )
        WR_D_A(0x24, ampl)
    #Update_CLK()
    
def Set_ramprate(N):
    WR_D_A(0x1a, N>>16)
    WR_D_A(0x1b, N>>8)
    WR_D_A(0x1c, N)
    

def SingleTone(freq):
    Init_AD9854(0x00)
    on(freq)

def on(freq):
    Set_freq(freq,1095,addrF1)
    Update_CLK()
    led.on()
    
def off():
    Set_freq(0,0,addrF1)
    led.off()
    trigger.off()
    
def UFSK(freq1,freq2):
    fsk.off()
    Init_AD9854(0x2)
    Set_freq(freq1,1095,addrF1)
    Set_freq(freq2,-1,addrF2)
    Update_CLK()
    led.on()
    
def RUFSK(freq1,freq2,delta,N):
    fsk.off()
    Init_AD9854(0x4)
    Rst_ACC(2,0x4)
    # Sets Ramped FSK with triangle ramp shape
    if freq1 < freq2:
        # Set initial freq
        Set_freq(freq1,1095,addrF1)
        # Set final freq
        Set_freq(freq2,-1,addrF2)
    else :
        # Set initial freq
        Set_freq(freq2,1095,addrF1)
        # Set final freq
        Set_freq(freq1,-1,addrF2)
    # Set frequency step
    Set_freq(twos_comp(delta, 48),-1,addrDelta)
    # Set period (N+1)*System CLK
    Set_ramprate(N)
    Update_CLK()
    led.on()
    
def Switch():
    fsk.toggle()
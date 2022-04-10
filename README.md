# PicoDDS
A Raspberry Pico PCB board that can interface with the AD9854 (and similar others) DDS chips or evaluation boards through parallel port.
<br/>
## Why ?
This project was inspired by the necessity of having a simple python/serial interface to easily control older DDS evaluation boards (e.g. AD9854).
<br/>
The [Eval-AD9854](https://www.analog.com/en/design-center/evaluation-hardware-and-software/evaluation-boards-kits/EVAL-AD9854.html "Eval-AD9854") is an "old" evaluation board for the [AD9854](https://www.analog.com/en/products/ad9854.html "AD9854") Analog Devices DDS IC. The board permits programming of the AD9854 through a serial or parallel interface. 
<br/><br/>
While the AD9854 is still alive and in production at the time of writing, the word "old" refers to the serial port interface used in the Eval-AD9854 boards. 
<br/>
Even though the provided software is not compatible with current Microsoft windows version the hardest part of programming the evaluation board comes from finding a parallel printer cable, perhaps from some electronics "museum".

<br/>
If you are wondering what the parallel printer port on the Eval-AD9854 looks like, here it is:

![Parallel_printer](/images/Printer_port.jpg?raw=true "Parallel printer connection for millenials and older")

Lukily this is not the only interface for programming the evaluation board. A 40 pins IDE port is also available on the board:

![40_pins_port](/images/40_pins_port.jpg?raw=true "The 40 pins IDE port on the Eval-AD99854 board")

This looks like a perfect match for any Raspberry Pi board! A custom cable from a Raspberry Pi 3/4 to the Eval-9854 board could be made (as I did for the first prototyping), but this will require a cable per each DDS and a lot of soldering. 
A better idea would be to design a PCB board that interfaces a Raspberry Pi with the DDS evaluation board.
## Why the Pico ? Can I use any Raspberry Pi ?

Sure, any microcontroller capable of handling 21 digital pins can do the job. I decided on  a Raspberry Pico just because of its price tag and small form factor.

## How about powering up the board? 

The evaluation board needs a 3.3V power source to operate. This can also be provided by the same Raspberry. **BEWARE** The Eval-9854 can request up to 1A of power, not all Raspberry pi boards can source that amount of power. When not using the sinc filtering function of the DDS the power consumption goes reduces to ~750mA, when prototyping I used a Raspberry pi 400 and it handled the power hungry DDS quite decently. I would however suggest to power this boards externally. The PCB board in this repository takes care also of that. I added a 1A LDO with a screw terminal where one can connect power cables to the Eval-9854; not very elegant, I know,but practical. 

## How to load the "firmware" on the board ? 

Once you are in possession of a PicoDDS board you will have to load on the Raspberry Pico the python source file that you find in the /src folder. The programming of the Pico happens through its micro USB connection. **The USB connection on the board is only for powering the Pico and the Eval-9854; it cannot be used to transfer data to the board!!**

![PCB_top|400](/images/Pico_adapter_top.png?raw=true "PCB board + Raspberry Pico for AD9854")

## How to program the AD9854 ? 

The AD9854 permits various modes of operation:
- Single tone mode : in this mode we output a single pre-programmed frequency
- FSK : In this mode it is possible to switch between two pre-programmed frequencies
- Ramped FSK : As the previous but with ramping the frequency up/down when switching
- Chirp : A.k.a. as pulsed FM mode, starting from an initial frequency it ramps up (linearly or not linearly) for the programmed time.
- BPSK : Select between two pre-programmed phase offsets

More precise description can be found on the AD9854 datasheet.

<br/>

My tipycal day usage of the AD9854 is to drive some AOM in our laboratory (check out here why we want to do that : [hyqs](http://hyqs.nl/ "Hyqs")).
<br/>
<br/>
An [AOM](https://www.rp-photonics.com/acousto_optic_modulators.html "AOM") (Acousto Optic Modulator) is nothing more than a cyrstal vibrating at a certain frequency capable of steering a laser beam and adding-subtracting its resonating frequency to the diffracting beam (read more here ).
<br/>
The typical resonating frequencies of AOM are between 70-300MHz although the coverage of this bandwith is mostly wavelength dependent. In my case I need a signal at 150MHz and I appear to have some AD9854 around, in the future I plan to develop a board for a more updated DDS with integrated ns-swtiches.

## Clocking the AD9854

One of the parameters hard coded in the main.py file is the clocking speed. The AD9854 can be clocked at 300MHz max. It has an internal PLL clock multiplier in case only slower clocks are available. The board I've been using so far has a 60MHz oscillator on it, however for more phase-dependent applications I plan to use a 10MHz clock reference from an atomic clock in future. The maximum clock multiplier is 20 that would mean that using directly a 10MHz clock and a x20 multiplier will push my clocking speed to 200MHz (too low to output a 150MHz signal). In this case one can use a second DDS to generate a higher frequency clock or a second PLL clock multiplier.

Set the following variables depending on your clocking speed :
- SYSCLK : Provided clock speed (frequency of whatever you connect to the clock input port). In my case SYSCLK = 60E6.
- CLKMULT : Clock multiplier value, this will define the maximum frequency that can be generated by the DDS. In my case CLKMULT = 4 --> I'm clocking the DDS at 4*60MHz = 240MHz frequency and the highest output frequency I can get is 120MHz.
- WR_D_A(0x20, 0x60) : This is defined inside the _Init_AD9854()_ function. If you want to enable sinc filtering, replace it to _WR_D_A (0x20, 0x60) **BEWARE :** ** This raises the total power consumption to 1.1A (1A AD9854 + 100mA for the Pico), which is 100mA higher than the on-board LDO's capability. It should be enabled only when the Pico is connected through its micro-usb connection. In this configuration the mossfet will set the micro-usb as power source for the Pico and avoid over-loading the LDO. I will provide soon a V2 of the board with an updated LDO that can output up to 1.5A.
## How to use the micropython script

Various functions are available from the source script. These don't cover all the capabilities of the AD9854 but only what I need in the lab. More functions might be added in the future if I need them. Feel free to fork this repository if you want to add more!
<br/>
<br/>
After connecting to the Pico the following functions are available from the serial terminal.

- on(freq,ampl) : Turns on the AD9854 at the input frequency. freq must be declared in hertz. This corresponds to the single tone mode of the DDS. The amplitude of the signal can be selected with the "ampl" parameter [0-4095].
- off() : Turns off the DDS output (sets it to the lowest amplitude)
- UFSK(freq1, freq2, ampl) : Sets the AD9854 in FSK mode, the lowest frequency between freq1 and freq2 will be outputted immediately. To switch between the two frequencies one can use the Switch() function
- RUFSK(freq1, freq2, ampl, delta, N) : Switches between freq1 and freq2 going through a linear ramp between the two. This corresponds to the ramped-FSK mode of the DDS. N is the number of steps the counter will need before switching to the next frequency. The switching period is given by (N-1)*system_clock. "delta" is the frequency step incremented each time the counter reaches 0
- Switch() : Switches between freq1 and freq2

## No, I don't want to order your board!

Then no problem, the board just simplifies the connection. If you don't want to order a board or just test if the DDS works for you or any other reasons you can just connect 20 of the 40 pins connection to your Raspberry Pico (or 3/4) and start using generating RF frequencies immediately!
<br/>
<br/>
**BEWARE :** powering the DDS is now up to you. Find a 3.3V 1A power source (better if 1.5A).
<br/>
<br/>
Connect the Pico and the Eval-9854 as following:


- GP16 -> MRESET
- GP15 -> OSK
- GP17 -> PMODE
- GP14 -> RDB
- GP18 -> WRB
- GP13 -> I/O UD
- GP2 -> FSK (this can be found on the pin W9 on the board)
- GP19 -> A0
- GP12 -> A1
- GP20 -> A2
- GP11 -> A3
- GP21 -> A4
- GP10 -> A5
- GP22 -> D0
- GP9 -> D1
- GP8 -> D2
- GP7 -> D3
- GP6 -> D4
- GP5 -> D5
- GP4 -> D6
- GP3 -> D7

Or replace the Pins number in the python source file. A Raspberry pico can be connected using dupont wires as following :

![Pico_no_board|400](/images/Pico_no_board.jpg?raw=true "A Raspberry Pico connected to an Eval-AD9854 using dupont wires")

Notice the black wire going on the pin W9, this is used for the FSK bit.

## Performances

### Switching time :

Time required to switch off -> on the RF signal.
It takes ~6ms from the moment one calls the _on(freq,ampl)_ (T=0 in the picture) to the moment when the AD9854 gives an output. 
![Switching time](/images/Switching_time.jpg?raw=true "On/Off switching time")

### Frequency sweep :

This is an example of a frequency sweep :

![Frequency sweep](/images/Frequency_sweep.jpg?raw=true "Frequency sweep")

# LLM-based AI Agent for Sizing of Analog and Mixed Signal Circuit

### Introduction

This project introduces an LLM-based AI agent designed to assist with sizing in analog and mixed-signal (AMS) circuit design. By integrating large language models (LLMs) with Ngspice simulation and custom data analysis functions, and employing prompt engineering strategies, the agent effectively optimizes circuits to meet specified performance metrics.
The tool takes as input a SPICE-based netlist and natural language performance specifications, and outputs both an iterative optimization process and the final optimized netlist. You can visualize and track the optimization history and verify the robustness of the final design using the provided variation test. Multiple LLMs are supported and can be selected by the user.

### Key Features

**AI-assisted sizing recommendations**: Get LLM-generated suggestions for transistor dimensions based on your circuit specifications
**SPICE-compatible output**: Generates netlists compatible with popular circuit simulators ngspice.
**Simulation in-loop**: Achieved by LLM function calling. All the functions are corresponding to specific metrics and are pre-defined in the agent by the developer.
**Performance-aware iterative optimization**: Considers the required key AMS metrics (gain, bandwidth, power, etc.) during sizing. A result history is also used to provide a highly relevant context to enable effective in-context learning.

### Getting Started

##### Available Metrics
| Metric            | Description                          | Target Syntax Example | Units  |
|-------------------|--------------------------------------|-----------------------|--------|
| `ac_gain`         | Small-signal voltage gain            | `>60`                 | dB     |
| `tran_gain`       | Large-signal transient gain          | `>55`                 | dB     |
| `phase_margin`    | Stability margin                     | `>60`                 | °      |
| `power`           | Total power consumption              | `<2`                  | mW     |
| `THD`             | Total harmonic distortion            | `<1`                  | %      |
| `CMRR`            | Common-mode rejection ratio          | `>80`                 | dB     |
| `output_swing`    | Maximum output voltage range         | `>1.5`                | V      |
| `offset`          | Input-referred offset voltage        | `<5`                  | mV     |
| `ICMR`            | Input common-mode range              | `>1.5`                | V      |
| `bandwidth`       | -3dB bandwidth                       | `>100`                | MHz    |
| `unity_bandwidth` | Unity-gain bandwidth                 | `>200`                | MHz    |

##### Available Circuits
| Circuit                       | Description                                               | Number of Transistors |
|-------------------------------|-----------------------------------------------------------|-----------------------|
| `R_load.cir`                  | Basic amplifier with resistor load                        | `1`                   |
| `diode_load.cir`              | Basic amplifier with diode connected load                 | `2`                   |
| `inverter.cir`                | Inverter                                                  | `2`                   |
| `nand.cir`                    | Nand gate                                                 | `4`                   |
| `osc3.cir`                    | 3 Stages Ring Oscillator                                  | `6`                   |
| `ota.cir`                     | 5 transistor OTA with buffer output                       | `7`                   |
| `telescope_cascode.cir`       | Telescope cascode amplifier                               | `9`                   |
| `xor.cir`                     | XOR gate                                                  | `12`                  |
| `complementary_classAB_opamp` | Complementary input stage and class AB output stage opamp | `20`                  |


##### Basic Usage
1. Choose a LLM model from Claude 3 family, GPT 4o and 40 mini, and gemini 2.0 are available in the corresponding folder. Include api key and url in your environment.
**Example**: add 'API_KEY= <your api key> ' in enviroment or define it in notebook as 'api_key = <your api key>'. 
2. Find a netlist in folder [netlist](/home/chang/Documents/LLM-transistor-sizing/initial_circuit_netlist) or prepare your own circuit netlist (SPICE format).
3. Specify your performance constraints from available metrics and input to to 'User input' block.
4. Run the LLM-sizing tool and get the results.
5. Further verify the circuit by a variation test in folder [variation](/home/chang/Documents/LLM-transistor-sizing/variation)

### Evaluation of LLMs

We evaluated the performance of different LLMs to assess their applicability and optimization effectiveness across seven basic circuits. 

![Performance comparison of different LLMs](/home/chang/Documents/LLM-transistor-sizing/figures/performance.png)  

*Fig. 1. Performance comparison of different LLMs.*

### Example 

**User input**:
"This is a circuit netlist, optimize this circuit with a output swing above 1.7V, input offset smaller than 0.001V, input common mode range bigger than 1.6, ac gain and transient gain above 60dB, unity bandwidth above 10000000Hz, phase margin bigger than 50 degree, power smaller than 0.05W, cmrr bigger than 100dB and thd small than -26dB"

**Netlist**: [Complemention classAB opamp](/home/chang/Documents/LLM-transistor-sizing/initial_circuit_netlist/complementary_classAB_opamp.cir)

**Result history**:

![Optimization results for the opamp.](/home/chang/Documents/LLM-transistor-sizing/figures/railtorail_subplots_4x2.png)

*Fig. 2. Optimization results for the opamp.  (a) Gain (b) Unity-Gain Bandwidth (c) Phase Margin (d) Power (e) Input Offset (f) Output Voltage Range (g) CMRR (h) THD. (b) and (e) are tested under unity gain configuration, others are tested open loop. (a), (b), (c), (d) and (g) are tested at Vin,cm = 0.9 V, (e), (f), (h) are tested across the Vin from 0 to 1.8 V. Those already in the target range initially or after a few iterations may still fluctuate or even get worse due to the optimization process prioritizing other performance metrics. This occurs because the agent has not yet achieved a balance between all required performance criteria*

**Output netlist**: [Optimization netlist](/home/chang/Documents/LLM-transistor-sizing/variation/a5.cir)

**Variation Results**:

![Variation results.](/home/chang/Documents/LLM-transistor-sizing/figures/a5_bias_var_subplots.png) 

*Fig. 3. Variation results.  (a) Input Offset Voltage vs. Common-Mode Input. (b) DC Gain vs. Output Voltage (c) DC Gain vs. Load Resistor. (d) CMRR vs. Common Mode Input. Random variations following a Gaussian distribution with a mean (µ) of 0 and a standard deviation (σ) of 0.1 are added to bias voltages and σ of 0.01 for transistor size.*

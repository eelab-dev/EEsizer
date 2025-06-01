# LLM-based AI Agent for Sizing of Analog and Mixed Signal Circuit

## Introduction

This project introduces an LLM-based AI agent designed to assist with sizing in analog and mixed-signal (AMS) circuit design. By integrating large language models (LLMs) with Ngspice simulation, custom data analysis functions, and employing prompt engineering strategies, the agent effectively optimizes circuits to meet specified performance metrics.
The tool takes as input a SPICE-based netlist and natural language performance specifications, and outputs both an iterative optimization process and the final optimized netlist. You can visualize and track the optimization history and verify the robustness of the final design using the provided variation test. Multiple LLMs are supported and can be selected by the user.

## Key Features

1. AI-assisted sizing: Get LLM-generated suggestions for transistor dimensions based on input specifications
2. SPICE-compatible output: Generates netlists compatible with popular circuit simulators ngspice.
3. Simulation in-loop: Achieved by LLM function calling. All the functions are pre-defined in the agent.
4. Performance-aware iterative optimization: Considers the required key AMS metrics during sizing. Result history is also used to provide a highly relevant context to enable effective in-context learning.

## Getting Started

### Available Metrics
| Metric            | Description                          | Target Example        | Units  |
|-------------------|--------------------------------------|-----------------------|--------|
| `ac_gain`         | Small-signal voltage gain            | `>60`                 | dB     |
| `tran_gain`       | Large-signal transient gain          | `>55`                 | dB     |
| `phase_margin`    | Stability margin                     | `>60`                 | °      |
| `power`           | Total power consumption              | `<0.002`                  | W     |
| `THD`             | Total harmonic distortion            | `<-26`                  | dB      |
| `CMRR`            | Common-mode rejection ratio          | `>80`                 | dB     |
| `output_swing`    | Maximum output voltage range         | `>1.5`                | V      |
| `offset`          | Input-referred offset voltage        | `<0.005`                  | V     |
| `ICMR`            | Input common-mode range              | `>1.5`                | V      |
| `bandwidth`       | -3dB bandwidth                       | `>10000`                | Hz    |
| `unity_bandwidth` | Unity-gain bandwidth                 | `>20000`                | Hz    |

### Available Circuits(please find in [netlist](/initial_circuit_netlist))
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
| `complementary_classAB_opamp.cir` | Complementary input stage and class AB output stage opamp | `20`                  |


### Basic Usage
1. Choose a LLM model from Claude 3 family, GPT 4o and 40 mini, and gemini 2.0 are available in the corresponding folder. Include api key and url in your environment.
2. Find a netlist in [netlist](/initial_circuit_netlist) or prepare your own circuit netlist (SPICE format).
3. Specify your performance constraints from available metrics and input to to 'User input' block.
4. Run the LLM-sizing tool and get the results.
5. Further verify the circuit by a variation test in [variation](/variation)

## Example 

'''User input:    

"This is a circuit netlist, optimize this circuit with a output swing above 1.7V, input offset smaller than 0.001V, input common mode range bigger than 1.6, ac gain and transient gain above 60dB, unity bandwidth above 10000000Hz, phase margin bigger than 50 degree, power smaller than 0.05W, cmrr bigger than 100dB and thd small than -26dB"

'''

**Netlist**: [Complemention classAB opamp](/initial_circuit_netlist/complementary_classAB_opamp.cir)

### Model Output:

**Output netlist**: [Optimized netlist](/variation/a5.cir)

**Result history**:

![Optimization results for the opamp.](/figures/railtorail_subplots_4x2.png)

### Variation Results:

![Variation results.](/figures/a5_bias_var_subplots.png) 

## Evaluation of LLMs

We evaluated the performance of different LLMs to assess their applicability and optimization effectiveness across seven basic circuits. 

![Performance comparison of different LLMs](/figures/performance.png)  
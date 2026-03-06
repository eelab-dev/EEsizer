# EEsizer: LLM-based AI Agent for Sizing of Analog and Mixed Signal Circuit

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
1. Choose a LLM model from [Claude 3 family](/agent_test_claude/agent_claude3.5.ipynb), [GPT 4o](/agent_test_gpt/agent_4o.ipynb) and [4o mini](/agent_test_gpt/agent_4omini.ipynb), and [gemini 2.0](/agent_test_gemini/gemini_2.0.ipynb) are available in the corresponding folder. 
Please add your api key and url in .env use the format below:
```
API_URL="your url"
API_KEY=your api
```
2. Find a netlist in [available netlist](/initial_circuit_netlist) or prepare your own circuit netlist (SPICE format) and load it to netlist input:
```
with open('../initial_circuit_netlist/complementary_classAB_opamp.cir', 'r') as f:
    netlist = f.read() 
```
or copy and paste it to variable 'netlist'.

3. Specify your performance constraints from available metrics and input to 'User input' block and input to variable:
```
tasks_generation_question = "This is a circuit netlist, optimize this circuit with ... "
```
4. Run the LLM-sizing tool and get the results.
5. Further verify the circuit by a variation test in [variation](/variation)

## Example 

**Model**: [Gemini 2.0 lite](/agent_test_gemini/gemini_2.0.ipynb)

**User input**:    
```

tasks_generation_question = "This is a circuit netlist, optimize this circuit with a output swing above 1.7V, input offset smaller than 0.001V, input common mode range bigger than 1.6, ac gain and transient gain above 60dB, unity bandwidth above 10000000Hz, phase margin bigger than 50 degree, power smaller than 0.05W, cmrr bigger than 100dB and thd small than -26dB"

```

**Netlist**: [Complemention classAB opamp](/initial_circuit_netlist/complementary_classAB_opamp.cir)

### Model Output:

**Output netlist**: [Optimized netlist](/variation/a5.cir)

**Result history**:

![Optimization results for the opamp.](/figures/rail-to-rail-process.png)

### Variation Results:

![Variation results.](/figures/monte-carlo-10var.png) 

## Evaluation of LLMs

We evaluated the performance of different LLMs to assess their applicability and optimization effectiveness across seven basic circuits. 

![Performance comparison of different LLMs](/figures/performance-new.png) 

## Updated results

Performance evaluation for five attempts across three groups (G1, G2, and G3). A 5% tolerance is applied to all metrics; deviations beyond this tolerance are shown in <span style="color:red">red</span>. Different targets for G1 vs G2 and G1 vs G3 are shown in **bold**. For G1 and G3, a load capacitor `C_L = 10 pF` and load resistor `R_L = 1 kOhm` are considered. For G2, a load capacitor `C_L = 50 pF` and load resistor `R_L = 100 kOhm` are considered. If the 25th iteration is reached without meeting any of the targets, it is marked as a failure.

| Group | Iter. | Gain (dB) | UGBW (MHz) | PM (deg) | Power (mW) | CMRR (dB) | THD (dB) | Offset (mV) | Output Swing (V) | ICMR (V) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <span style="color:blue">G1 Target</span> | <span style="color:blue">25</span> | <span style="color:blue">>=65</span> | <span style="color:blue">>=10</span> | <span style="color:blue">>=50</span> | <span style="color:blue"><=10</span> | <span style="color:blue">>=100</span> | <span style="color:blue"><=-26</span> | <span style="color:blue"><=1</span> | <span style="color:blue">1.2</span> | <span style="color:blue">1.2</span> |
| **G1 Initial** | **0** | **33.23** | **0.50** | **86.55** | <span style="color:green">0.46</span> | **55.93** | **-28.35** | **176** | **0.21** | <span style="color:green">0.21</span> |
| G1-1 | **16** | 69.74 | 25.12 | 70.74 | <span style="color:green">4.05</span> | 102.36 | <span style="color:green">-24.81</span> | 0.03 | 1.15 | <span style="color:green">1.15</span> |
| G1-2 | **20** | 69.14 | 19.95 | 77.01 | <span style="color:green">4.07</span> | 112.00 | <span style="color:green">-25.65</span> | 0.02 | 1.16 | <span style="color:green">1.15</span> |
| G1-3 | fail | <span style="color:red">59.21</span> | 79.43 | 76.57 | 0.61 | <span style="color:red">23.17</span> | -27.95 | 0.52 | <span style="color:red">0.95</span> | <span style="color:red">1.02</span> |
| G1-4 | fail | <span style="color:red">53.60</span> | 39.81 | 79.82 | 4.66 | <span style="color:red">36.28</span> | -25.52 | 0.18 | 1.15 | 1.19 |
| G1-5 | fail | <span style="color:red">34.09</span> | 10.00 | 61.97 | 1.74 | <span style="color:red">70.17</span> | -42.05 | <span style="color:red">11.34</span> | <span style="color:red">0.85</span> | <span style="color:red">0.97</span> |
| <span style="color:blue">G2 Target</span> | <span style="color:blue">25</span> | <span style="color:blue">>=65</span> | **<span style="color:blue">>= 5</span>** | **<span style="color:blue">>= 45</span>** | **<span style="color:blue"><= 5</span>** | <span style="color:blue">>=100</span> | <span style="color:blue"><=-26</span> | <span style="color:blue"><=1</span> | <span style="color:blue">1.2</span> | <span style="color:blue">1.2</span> |
| **G2 Initial** | **0** | **40.03** | **1** | **75.05** | <span style="color:green">0.37</span> | **46.61** | **-37.91** | **2.05** | **1.08** | <span style="color:green">1.06</span> |
| G2-1 | **20** | 65.83 | 12.59 | 61.26 | <span style="color:green">1.00</span> | 115.15 | -25.77 | 0.01 | 1.19 | 1.19 |
| G2-2 | fail | 66.36 | <span style="color:red">1.99</span> | 48.06 | 0.40 | 107.62 | -31.71 | 0.06 | <span style="color:red">1.04</span> | 1.15 |
| G2-3 | fail | <span style="color:red">47.04</span> | <span style="color:red">2.51</span> | <span style="color:red">36.19</span> | 0.40 | <span style="color:red">84.85</span> | -26.03 | 0.48 | 1.18 | 1.19 |
| G2-4 | fail | <span style="color:red">53.87</span> | 5.01 | <span style="color:red">42.23</span> | 1.52 | 98.18 | -25.62 | 0.12 | 1.19 | 1.19 |
| G2-5 | fail | <span style="color:red">57.23</span> | 6.31 | <span style="color:red">25.68</span> | 0.50 | <span style="color:red">46.76</span> | <span style="color:red">-23.41</span> | 0.14 | 1.19 | 1.19 |
| <span style="color:blue">G3 Target</span> | <span style="color:blue">25</span> | <span style="color:blue">>=65</span> | **<span style="color:blue">>=50</span>** | **<span style="color:blue">>=50</span>** | **<span style="color:blue"><=20</span>** | **<span style="color:blue">>=80</span>** | **<span style="color:blue"><=-26</span>** | <span style="color:blue"><=1</span> | <span style="color:blue">1.2</span> | <span style="color:blue">1.2</span> |
| **G3 Initial** | **0** | **33.23** | **0.50** | **86.55** | <span style="color:green">0.46</span> | **55.93** | **-28.35** | **176** | **0.21** | <span style="color:green">0.21</span> |
| G3-1 | **16** | 64.51 | 125.89 | 68.75 | <span style="color:green">4.39</span> | 103.68 | -32.60 | 0.24 | 1.14 | <span style="color:green">1.07</span> |
| G3-2 | fail | 66.67 | <span style="color:red">39.81</span> | <span style="color:red">37.09</span> | 4.23 | 103.50 | <span style="color:red">-21.05</span> | 0.69 | <span style="color:red">1.13</span> | 1.18 |
| G3-3 | fail | 75.34 | 125.89 | <span style="color:red">33.74</span> | 13.72 | 126.24 | <span style="color:red">-20.15</span> | 0.06 | 1.17 | 1.19 |
| G3-4 | fail | 67.68 | 63.09 | 51.55 | 3.69 | 120.84 | <span style="color:red">-18.39</span> | 0.09 | <span style="color:red">1.11</span> | 1.14 |
| G3-5 | fail | 66.67 | <span style="color:red">37.08</span> | <span style="color:red">39.81</span> | 4.00 | 103.51 | <span style="color:red">-21.08</span> | 0.07 | 1.14 | 1.18 |

# Publication

Please see [LLM-based AI Agent for Sizing of Analog and Mixed Signal Circuit](https://arxiv.org/abs/2504.11497). This work was presented in [NEWCAS2025](https://www.newcas2025.com/).

# Acknowledgements 

This work was made possible by Peter Denyer's PhD Scholarship at The University of Edinburgh.

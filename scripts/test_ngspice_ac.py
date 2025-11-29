import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from eesizer.sim.ngspice import NgSpiceSimulator
from eesizer.sim.base import SimulationRequest
from eesizer.io.paths import OUTPUT_DIR, out_path
from eesizer.analysis.metrics import ac_gain_db_from_dat

# Minimal RC low-pass with AC analysis
NETLIST = """
.title RC_LP
R1 in out 1k
C1 out 0 1u
Vin in 0 AC 1
.op
.end
"""

# Build a .control block inline
CONTROL = """
.control
  ac dec 10 1 1e6
  wrdata output_ac.dat out
.endc
"""

if __name__ == "__main__":
    nl = NETLIST.replace(".end", CONTROL + "\n.end")
    sim = NgSpiceSimulator(run_dir=OUTPUT_DIR)
    req = SimulationRequest(sim_type="ac", options={})
    res = sim.run(nl, req)
    assert res.success, f"Ngspice failed: {res.stderr}"
    ac_path = out_path("output_ac.dat", run_dir=OUTPUT_DIR)
    g = ac_gain_db_from_dat(ac_path)
    print("AC gain dB (at low freq):", g)

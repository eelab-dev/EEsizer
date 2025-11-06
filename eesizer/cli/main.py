import os
import typer
from typing import Optional, List
from ..sim.ngspice import NgSpiceSimulator
from ..sim.base import SimulationRequest
from ..sim.netlist_builders import build_ac_netlist
from ..analysis.metrics import ac_gain_db_from_dat, bandwidth_hz_from_dat, unity_bandwidth_hz_from_dat, phase_margin_deg_from_dat
from ..io.paths import OUTPUT_DIR

app = typer.Typer()


@app.command()
def simulate_ac(netlist: str, signals: List[str] = typer.Argument(["out"])):
    """Build an AC simulation around a SPICE netlist, run it, and print basic metrics.

    - signals: nodes to record with wrdata (default: out)
    """
    with open(netlist, "r") as f:
        base = f.read()
    # Build AC netlist that writes output_ac.dat under OUTPUT_DIR
    ac_netlist = build_ac_netlist(base, signals=signals, outfile="output_ac.dat", ac_cmd="ac dec 10 1 1e7")
    simreq = SimulationRequest(sim_type="ac", options={})
    sim = NgSpiceSimulator(run_dir=OUTPUT_DIR)
    result = sim.run(ac_netlist, simreq)
    if not result.success:
        typer.echo("Simulation failed")
        raise typer.Exit(code=1)
    ac_path = os.path.join(OUTPUT_DIR, "output_ac.dat")
    g = ac_gain_db_from_dat(ac_path)
    bw = bandwidth_hz_from_dat(ac_path)
    ugbw = unity_bandwidth_hz_from_dat(ac_path)
    pm = phase_margin_deg_from_dat(ac_path)
    typer.echo(f"AC Gain (dB): {g:.3f}")
    typer.echo(f"Bandwidth (Hz): {bw:.3e}")
    typer.echo(f"Unity BW (Hz): {ugbw:.3e}")
    typer.echo(f"Phase Margin (deg): {pm:.2f}")


if __name__ == "__main__":
    app()

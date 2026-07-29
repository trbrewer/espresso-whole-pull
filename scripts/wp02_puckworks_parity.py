#!/usr/bin/env python3
"""One-shot locked-Puckworks parity runner; compact output only."""
from __future__ import annotations
import argparse, hashlib, importlib, json, math, sys
from pathlib import Path
np = importlib.import_module("numpy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import waszkiewicz_effective_permeability as local
from wp02_phi_decimal_reference import decimal_phi_factor

def h(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--checkout",type=Path,required=True); ap.add_argument("--protocol-sha256",required=True); ap.add_argument("--output",type=Path,required=True); a=ap.parse_args()
    sys.path.insert(0,str(a.checkout))
    from puckworks.models.waszkiewicz2025 import poroelastic as ref
    s=dict(pc_bar=12.391550000000002,qc_g_s=1.8969919954879988,k_g=2.257390325360356,l_s=19.833265422011824,m_s=9.341259347305948,dose_g=18.5)
    t=np.linspace(0,100,1000); md=ref.solids_sigmoid(t,s["k_g"],s["l_s"],s["m_s"]); phis=md/s["dose_g"]; phim=s["k_g"]/s["dose_g"]
    def phi_stats(vals):
        r=ref.phi_factor(vals); l=np.array([local.phi_factor(float(x)) for x in vals]); ae=np.abs(l-r); re=ae/np.abs(r)
        ia=int(np.argmax(ae)); ir=int(np.argmax(re))
        return {"point_count":len(vals),"phi_minimum":float(np.min(vals)),"phi_maximum":float(np.max(vals)),"maximum_absolute_error":float(ae[ia]),"maximum_relative_error":float(re[ir]),"worst_absolute_phi":float(vals[ia]),"worst_relative_phi":float(vals[ir])}
    operational=phi_stats(np.append(phis[100:],phim)); complete=phi_stats(phis)
    qpoints=np.array([.01,.1,.5,.9,1.]); qabs=float(np.max(np.abs(np.array([local.qhat(float(x)) for x in qpoints])-ref.qhat(qpoints))))
    static=max(abs(local.q_static(p,s["pc_bar"],s["qc_g_s"])-float(ref.q_static(p,s["pc_bar"],s["qc_g_s"])))/abs(float(ref.q_static(p,s["pc_bar"],s["qc_g_s"]))) for p in (8.,9.))
    mdl=np.array([local.solids_sigmoid(float(x),s["k_g"],s["l_s"],s["m_s"]) for x in t]); mdrel=float(np.max(np.abs((mdl-md)/md)))
    dynamics={}
    clip=True
    for p in (8.,9.):
        r=ref.q_dynamic(t,p,s["pc_bar"],s["qc_g_s"],s["k_g"],s["l_s"],s["m_s"],s["dose_g"]); l=np.array(local.vector_dynamic(t,p,**s)); nz=r!=0
        dynamics[str(int(p))]={"maximum_absolute_error_g_per_s":float(np.max(np.abs(l-r))),"maximum_relative_error":float(np.max(np.abs((l[nz]-r[nz])/r[nz])))}
        clip=clip and bool(np.array_equal(l==0,r==0))
    p=1e-4; lv=local.phi_factor(p); pv=float(ref.phi_factor(p)); dv=float(decimal_phi_factor("1e-4"))
    off={"phi":p,"classification":"REFERENCE_CANCELLATION_DIAGNOSTIC_OUTSIDE_SOURCE_DOMAIN","acceptance_role":"DIAGNOSTIC_ONLY","local":lv,"decimal":dv,"puckworks":pv,"local_puckworks_absolute_error":abs(lv-pv),"local_puckworks_relative_error":abs(lv-pv)/abs(pv),"puckworks_decimal_absolute_error":abs(pv-dv)}
    mandatory=operational["maximum_absolute_error"]<=1e-14 and operational["maximum_relative_error"]<=1e-8 and complete["maximum_absolute_error"]<=1e-14 and qabs<=1e-12 and static<=1e-12 and mdrel<=1e-12 and all(x["maximum_absolute_error_g_per_s"]<=1e-10 and x["maximum_relative_error"]<=1e-8 for x in dynamics.values()) and clip
    out={"schema_version":"espresso.public.wp02_001_source_parity.v2","protocol_sha256":a.protocol_sha256,"puckworks":{"commit":"fc61c4670ec7bf801e40bb391aab16048b8da26b","tree":"1d553e44ee2f7480a5df521560801b478618cc84"},"operational_phi_factor":operational,"complete_grid_phi_factor":{**complete,"relative_error_gate_applied":False},"off_domain_diagnostic":off,"qhat_maximum_absolute_error":qabs,"static_flow_maximum_relative_error":static,"dissolved_mass_maximum_relative_error":mdrel,"dynamic_flow":dynamics,"clipping_exact":clip,"overall_source_parity":"PASS" if mandatory else "FAIL"}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if mandatory else 1
if __name__=="__main__": raise SystemExit(main())

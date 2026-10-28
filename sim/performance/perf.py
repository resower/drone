"""CF-2 Rev-C performance ESTIMATES (first-principles, best case unless stated). Not measurements."""
import json, math
rho=1.225; g=9.81
m=2.0                      # kg, see bom_revc.py mass table (estimate +-15 %)
Wh_nom=22.2*1.4; Wh=Wh_nom*0.85        # 6S 1400 mAh, 85 % usable
A=math.pi*0.0635**2        # 5.1 in prop disc
out={}
# hover
T=m*g/4; Pid=T**1.5/math.sqrt(2*rho*A); FM=0.55; eta=0.80
Phov=4*Pid/FM/eta+25
out['hover']=dict(P_W=round(Phov), min=round(Wh/Phov*60,1))
# normal flight 50 km/h, best case: translational-lift saving 25 %, small drag term
v=50/3.6; CdA=0.04; Pd=0.5*rho*v**3*CdA/0.6
Pc=0.75*Phov+Pd
out['cruise50']=dict(P_W=round(Pc), min=round(Wh/Pc*60,1), km=round(v*Wh/Pc*3600/1000,1))
# rover 18 km/h
v=18/3.6; Crr=0.04; Pm=Crr*m*g*v/0.5; Pr_best=Pm+8+5; Pr_typ=Pm+8+25
out['rover']=dict(P_best_W=round(Pr_best), P_typ_W=round(Pr_typ), km_best=round(v*Wh/Pr_best*3600/1000,1), km_typ=round(v*Wh/Pr_typ*3600/1000,1), min_best=round(Wh/Pr_best*60))
# speed mode
def speed(kmh, CdA, etap):
    v=kmh/3.6; q=0.5*rho*v*v; D=q*CdA*1.0+q*0.06*0.02+1.0   # body/ring drag + wing profile + induced allowance
    Pa=D*v; Pe=Pa/etap/1.0+20
    return dict(D_N=round(D,1), P_W=round(Pe), I_A=round(Pe/22.2), min=round(Wh*0.8/Pe*60,1), km=round(v*Wh*0.8/Pe*3600/1000,1))
out['speed100_best']=speed(100,0.02,0.5)
out['speed100_typ']=speed(100,0.03,0.45)
out['speed150_best']=speed(150,0.02,0.45)
out['speed150_typ']=speed(150,0.03,0.40)
# thrust available at 150 km/h, assuming 30 % of static (generic ratio, earlier note) and static 1.9 kg per motor
Tst=4*1.9*g; out['thrust150_avail_N']=round(0.30*Tst,1)
out['wing_area_cm2_150']=round(m*g/(0.5*rho*(150/3.6)**2*0.5)*1e4); out['wing_area_cm2_100']=round(m*g/(0.5*rho*(100/3.6)**2*0.5)*1e4)
out['battery_Wh_usable']=round(Wh,1)
json.dump(out,open('perf.json','w'),indent=1); print(json.dumps(out,indent=1))

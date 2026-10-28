"""CAD-volume mass estimate (ESTIMATES: density x fill factor are assumptions; placeholders use catalogue-class masses) + CG per configuration."""
import json, numpy as np, library, assemble, kin
from params import P

def part_table():
    L = library.lib(); rows = {}
    for n, d in L.items():
        sh = d['shape']; v = sh.Volume()/1000.0       # cm3
        dens, fill = library.MAT[d['material']]
        if d['mass_g'] is not None: m = d['mass_g']; basis = 'placeholder (catalogue-class assumption)'
        else: m = v*dens*fill; basis = 'CAD volume x density %.2f x fill %.2f (assumed)' % (dens, fill)
        c = sh.Center(); rows[n] = dict(vol_cm3=v, mass_g=m, basis=basis, com_local=[c.x, c.y, c.z], material=d['material'], group=d['group'], placeholder=d['placeholder'])
    return rows

def config_cg(cfg, rows=None):
    rows = rows or part_table(); tot = 0.0; acc = np.zeros(3); per = {}
    for i in assemble.instances(cfg):
        r = rows[i['part']]; m = r['mass_g']
        if 'mirror' in i:
            c = np.array(r['com_local'])
            if kin.SY[i['mirror']] < 0: c[1] = -c[1]
            if kin.SX[i['mirror']] < 0: c[0] = -c[0]
            w = c
        else:
            T = i['T']; w = T[:3, :3] @ np.array(r['com_local']) + T[:3, 3]
        tot += m; acc += m*w; per.setdefault(i['group'].split('_')[0].split('/')[0], 0.0); per[i['group'].split('_')[0].split('/')[0]] += m
    return tot, acc/tot, per

if __name__ == '__main__':
    rows = part_table(); out = {'parts': rows}
    for name in ('cfg_flight', 'cfg_ground', 'cfg_compact'):
        tot, cg, per = config_cg(P[name], rows); out[name] = dict(mass_g=tot, cg=cg.tolist(), by_group=per)
        print(name, 'mass %.0f g' % tot, 'CG', np.round(cg, 1), {k: round(v) for k, v in per.items()})
    json.dump(out, open('../build/mass_cg_v2.json', 'w'), indent=1)

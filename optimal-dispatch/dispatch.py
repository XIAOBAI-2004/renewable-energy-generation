"""Islanded PV/wind/storage dispatch extension; MW, MWh and hours.

Synthetic teaching cases, not measurements or a closed-loop Simulink run.
Both comparisons optimize storage. Only the flexible-load time window changes.
"""
from pathlib import Path
import json
import os
import time
from dataclasses import dataclass, asdict

HERE = Path(__file__).resolve().parent
CACHE = Path(os.environ.get('COURSE_TEMP_DIR', '/temp')) / 'renewable-energy' / 'wind-pv-storage-dispatch'
CACHE.mkdir(parents=True, exist_ok=True)
os.environ['TMPDIR'] = str(CACHE)
os.environ['MPLCONFIGDIR'] = str(CACHE / 'matplotlib')
os.environ['MPLBACKEND'] = 'Agg'

import cvxpy as cp
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Settings:
    dt_h: float = 1.0
    pv_rating_mw: float = 5.0
    wind_rating_mw: float = 5.0
    pv_pf: float = 0.9
    battery_power_mw: float = 5.0
    battery_energy_mwh: float = 10.0
    battery_inverter_mva: float = 6.0
    soc_initial: float = 0.60
    soc_min: float = 0.15
    soc_max: float = 0.90
    efficiency_charge: float = 0.96
    efficiency_discharge: float = 0.96
    flex_power_mw: float = 1.5
    load_q_per_p: float = 0.23
    capacitor_mvar: float = 0.2
    battery_cost_yuan_per_mwh: float = 80.0
    curtailment_cost_yuan_per_mwh: float = 20.0
    shift_cost_yuan_per_mwh: float = 30.0


SETTINGS = Settings()
SCENARIOS = {
    'normal': (1.0, 1.0, 1.0),
    'low_pv': (0.65, 1.0, 1.0),
    'low_wind': (1.0, 0.90, 1.0),
    'high_load': (1.0, 1.0, 1.12),
    'combined_stress': (0.50, 0.85, 1.05),
}


def make_inputs(scenario, cfg=SETTINGS):
    """Deterministic, shared base profile; variants modify stated factors only."""
    pv_factor, speed_factor, load_factor = SCENARIOS[scenario]
    h = np.arange(24)
    irradiance = np.maximum(0, np.sin(np.pi * (h - 6) / 12)) ** 1.6
    v = np.array([10.5, 10.5, 10.2, 10, 9.8, 9.5, 9.2, 8.8, 8.5, 8.4,
                  8.6, 8.8, 9, 9.2, 9.5, 9.8, 10, 10.3, 11.2, 11.4,
                  11.5, 11.6, 11.5, 11.4]) * speed_factor
    fixed = (3 + .9 * np.exp(-((h - 9) / 3) ** 2)
             + 1.4 * np.exp(-((h - 19) / 3) ** 2)) * load_factor
    preferred = np.zeros(24)
    preferred[9:12] = 1.0
    preferred[18:21] = 1.0
    return pd.DataFrame({
        'hour': h, 'pv_available_mw': cfg.pv_rating_mw * irradiance * pv_factor,
        'wind_speed_m_s': v,
        'wind_available_mw': np.minimum(cfg.wind_rating_mw, cfg.wind_rating_mw * (v / 12) ** 3),
        'fixed_load_mw': fixed, 'flex_preferred_mw': preferred,
        'flex_allowed_mw': np.where((h >= 8) & (h < 22), cfg.flex_power_mw, 0.0),
    })


def solve_dispatch(data, mode, cfg=SETTINGS):
    if mode not in ('fixed_time', 'optimized'):
        raise ValueError(mode)
    cols = ['pv_available_mw', 'wind_available_mw', 'fixed_load_mw',
            'flex_preferred_mw', 'flex_allowed_mw']
    a = data[cols].to_numpy()
    if len(data) == 0 or not np.isfinite(a).all() or (a < 0).any():
        raise ValueError('Input must contain finite, nonnegative power values.')
    if (data.pv_available_mw > cfg.pv_rating_mw + 1e-8).any():
        raise ValueError('PV availability exceeds nameplate.')
    if (data.wind_available_mw > cfg.wind_rating_mw + 1e-8).any():
        raise ValueError('Wind availability exceeds nameplate.')
    if 'SCIP' not in cp.installed_solvers():
        raise RuntimeError('SCIP is required; install the packages listed in the submission requirements.txt.')
    t = len(data)
    dt = cfg.dt_h
    pv = cp.Variable(t, nonneg=True)
    wind = cp.Variable(t, nonneg=True)
    charge = cp.Variable(t, nonneg=True)
    discharge = cp.Variable(t, nonneg=True)
    energy = cp.Variable(t + 1)
    charging = cp.Variable(t, boolean=True)
    flex = cp.Variable(t, nonneg=True)
    unserved = cp.Variable(t, nonneg=True)
    preferred = data.flex_preferred_mw.to_numpy()
    fixed = data.fixed_load_mw.to_numpy()
    pv_av = data.pv_available_mw.to_numpy()
    wind_av = data.wind_available_mw.to_numpy()
    task_mwh = preferred.sum() * dt
    delivered_flex = cp.sum(flex) * dt
    unserved_fixed = cp.sum(unserved) * dt
    unserved_flex = task_mwh - delivered_flex
    curt = pv_av + wind_av - pv - wind
    qpv = pv * np.tan(np.arccos(cfg.pv_pf))
    qbatt = cfg.load_q_per_p * (fixed - unserved + flex) - qpv - cfg.capacitor_mvar
    # This conservative rectangular capability constraint implies S_batt <= 6 MVA.
    q_limit = np.sqrt(cfg.battery_inverter_mva ** 2 - cfg.battery_power_mw ** 2)
    c = [pv <= pv_av, wind <= wind_av, unserved <= fixed,
         pv + wind + discharge - charge == fixed - unserved + flex,
         energy[0] == cfg.soc_initial * cfg.battery_energy_mwh,
         energy[-1] == energy[0],
         energy >= cfg.soc_min * cfg.battery_energy_mwh,
         energy <= cfg.soc_max * cfg.battery_energy_mwh,
         energy[1:] == energy[:-1] + dt * (cfg.efficiency_charge * charge
                                          - discharge / cfg.efficiency_discharge),
         charge <= cfg.battery_power_mw * charging,
         discharge <= cfg.battery_power_mw * (1 - charging),
         flex <= (preferred if mode == 'fixed_time' else data.flex_allowed_mw.to_numpy()),
         delivered_flex <= task_mwh, qbatt <= q_limit, qbatt >= -q_limit]
    started = time.perf_counter()
    statuses = []

    def solve(obj, cons):
        problem = cp.Problem(cp.Minimize(obj), cons)
        problem.solve(solver='SCIP', verbose=False,
                      scip_params={'numerics/feastol': 1e-9, 'limits/time': 60})
        statuses.append(problem.status)
        if problem.status != cp.OPTIMAL:
            raise RuntimeError(f'{mode}: solver status {problem.status}')
        return float(problem.value)

    # Service has strict priority over the illustrative economic weights.
    best_fixed = max(0.0, solve(unserved_fixed, c))
    c += [unserved_fixed <= best_fixed + 1e-7]
    best_flex = max(0.0, solve(unserved_flex, c))
    c += [unserved_flex <= best_flex + 1e-7]
    # Half L1 less uncompleted energy counts relocation, not task cancellation.
    shifted = (cp.norm1(flex - preferred) * dt - unserved_flex) / 2
    objective = (cfg.battery_cost_yuan_per_mwh * cp.sum(charge + discharge) * dt
                 + cfg.curtailment_cost_yuan_per_mwh * cp.sum(curt) * dt
                 + cfg.shift_cost_yuan_per_mwh * shifted)
    solve(objective, c)
    d = data.copy()
    for name, variable in [('pv_mw', pv), ('wind_mw', wind), ('charge_mw', charge),
                           ('discharge_mw', discharge), ('flex_mw', flex),
                           ('unserved_fixed_mw', unserved)]:
        d[name] = np.asarray(variable.value)
    d['battery_mw'] = d.discharge_mw - d.charge_mw
    d['soc_start'] = energy.value[:-1] / cfg.battery_energy_mwh
    d['soc_end'] = energy.value[1:] / cfg.battery_energy_mwh
    d['curtailment_mw'] = pv_av + wind_av - d.pv_mw - d.wind_mw
    d['load_served_mw'] = fixed - d.unserved_fixed_mw + d.flex_mw
    d['pv_q_mvar'] = np.asarray(qpv.value)
    d['battery_q_mvar'] = np.asarray(qbatt.value)
    d['power_residual_mw'] = d.pv_mw + d.wind_mw + d.battery_mw - d.load_served_mw
    if mode == 'fixed_time':
        assert (d.flex_mw <= data.flex_preferred_mw + 2e-6).all()
    task_short = max(0.0, float(task_mwh - d.flex_mw.sum() * dt))
    shifted_value = max(0.0, float((np.abs(d.flex_mw - preferred).sum() * dt - task_short) / 2))
    throughput = float((d.charge_mw + d.discharge_mw).sum() * dt)
    curtailment = max(0.0, float(d.curtailment_mw.sum() * dt))
    battery_cost = throughput * cfg.battery_cost_yuan_per_mwh
    curtailment_cost = curtailment * cfg.curtailment_cost_yuan_per_mwh
    shift_cost = shifted_value * cfg.shift_cost_yuan_per_mwh
    metrics = {
        'mode': mode, 'statuses': statuses, 'elapsed_seconds': time.perf_counter() - started,
        'available_renewable_mwh': float((pv_av + wind_av).sum() * dt),
        'fixed_demand_mwh': float(fixed.sum() * dt), 'flex_demand_mwh': task_mwh,
        'unserved_fixed_mwh': float(d.unserved_fixed_mw.sum() * dt),
        'uncompleted_flex_mwh': task_short, 'shifted_flex_mwh': shifted_value,
        'curtailment_mwh': curtailment, 'battery_throughput_mwh': throughput,
        'charge_mwh': float(d.charge_mw.sum() * dt), 'discharge_mwh': float(d.discharge_mw.sum() * dt),
        'battery_losses_mwh': float((d.charge_mw - d.discharge_mw).sum() * dt),
        'battery_cost_yuan': battery_cost, 'curtailment_cost_yuan': curtailment_cost,
        'shift_cost_yuan': shift_cost, 'dispatch_cost_yuan': battery_cost + curtailment_cost + shift_cost,
        'soc_min': float(np.min(energy.value) / cfg.battery_energy_mwh),
        'soc_max': float(np.max(energy.value) / cfg.battery_energy_mwh),
        'soc_final': float(d.soc_end.iloc[-1]),
        'max_balance_error_kw': float(np.max(np.abs(d.power_residual_mw)) * 1000),
        'max_battery_power_mw': float(np.max(np.abs(d.battery_mw))),
        'max_battery_apparent_mva': float(np.max(np.hypot(d.battery_mw, d.battery_q_mvar))),
    }
    audit(data, d, cfg)
    return d, metrics


def audit(inputs, d, cfg=SETTINGS):
    """Check physical identities independently of solver status."""
    tol = 2e-6
    assert np.max(np.abs(d.power_residual_mw)) < tol, 'power balance'
    energy_change = (d.soc_end - d.soc_start) * cfg.battery_energy_mwh
    expected = cfg.dt_h * (cfg.efficiency_charge * d.charge_mw - d.discharge_mw / cfg.efficiency_discharge)
    assert np.max(np.abs(energy_change - expected)) < tol, 'energy evolution'
    assert abs(d.soc_start.iloc[0] - cfg.soc_initial) < tol, 'initial SOC'
    assert abs(d.soc_end.iloc[-1] - cfg.soc_initial) < tol, 'terminal SOC'
    assert d.soc_end.min() >= cfg.soc_min - tol and d.soc_end.max() <= cfg.soc_max + tol
    assert d.charge_mw.max() <= cfg.battery_power_mw + tol
    assert d.discharge_mw.max() <= cfg.battery_power_mw + tol
    assert np.maximum(0, np.minimum(d.charge_mw, d.discharge_mw)).max() < tol, 'charge/discharge exclusivity'
    assert np.hypot(d.battery_mw, d.battery_q_mvar).max() <= cfg.battery_inverter_mva + tol
    assert np.hypot(d.pv_mw, d.pv_q_mvar).max() <= 6 + tol
    assert d.wind_mw.max() <= cfg.wind_rating_mw + tol
    assert (d.pv_mw <= inputs.pv_available_mw + tol).all()
    assert (d.wind_mw <= inputs.wind_available_mw + tol).all()
    assert (d.flex_mw <= inputs.flex_allowed_mw + tol).all()
    # With equal boundary SOC, renewable energy equals served load + curtailment + losses.
    left = (inputs.pv_available_mw + inputs.wind_available_mw).sum()
    right = (d.load_served_mw + d.curtailment_mw + d.charge_mw - d.discharge_mw).sum()
    assert abs(left - right) < tol, 'daily energy balance'


def plot_case(name, base, opt, out):
    """Save the experiment's original, unannotated figure; PPT embeds it unchanged."""
    h = opt.hour
    fig, ax = plt.subplots(2, 2, figsize=(20, 13), dpi=120)
    a, b, c, d = ax.flat
    a.plot(h, opt.pv_mw, label='PV dispatched', color='#E5AB00', linewidth=2)
    a.plot(h, opt.wind_mw, label='Wind dispatched', color='#347DB5', linewidth=2)
    a.plot(h, opt.battery_mw, label='Battery (+ discharge)', color='#419661', linewidth=2)
    a.plot(h, opt.fixed_load_mw + opt.flex_mw, label='Demand before shortage',
           color='#222222', linestyle='--', linewidth=1.5)
    a.plot(h, opt.load_served_mw, label='Load served', color='#222222', linewidth=2.5)
    a.set(title='Optimized power dispatch', ylabel='Power (MW)')
    b.step(h, base.flex_mw, where='post', label='Fixed-time schedule', color='#777777', linewidth=2)
    b.step(h, opt.flex_mw, where='post', label='Flexible schedule', color='#1866A0', linewidth=2)
    b.set(title='Flexible load', ylabel='Power (MW)', ylim=(-.05, 1.65))
    c.plot(np.arange(len(base) + 1), np.r_[base.soc_start.iloc[0], base.soc_end] * 100,
           label='Fixed-time schedule', color='#777777', linewidth=2)
    c.plot(np.arange(len(opt) + 1), np.r_[opt.soc_start.iloc[0], opt.soc_end] * 100,
           label='Flexible schedule', color='#1866A0', linewidth=2)
    c.set(title='Battery state of charge', ylabel='SOC (%)', ylim=(10, 95), xlim=(0, 24))
    d.bar(h - .18, base.curtailment_mw, width=.36, label='Fixed-time schedule', color='#999999')
    d.bar(h + .18, opt.curtailment_mw, width=.36, label='Flexible schedule', color='#1866A0')
    d.set(title='Wind and PV curtailment', ylabel='Power (MW)')
    for axis in ax.flat:
        axis.grid(True, alpha=.25)
        axis.set_xlabel('Hour')
        axis.set_xticks(np.arange(0, 25, 2))
        axis.legend(loc='best')
    fig.suptitle(f'Islanded Wind-PV-Storage Dispatch ({name})', fontsize=19)
    fig.tight_layout(rect=(0, 0, 1, .96))
    fig.savefig(out / f'dispatch_{name}.png')
    plt.close(fig)


def main():
    out = HERE / 'results'
    out.mkdir(exist_ok=True)
    (out / 'settings.json').write_text(json.dumps(asdict(SETTINGS), indent=2))
    summaries = []
    comparisons = []
    for name in SCENARIOS:
        data = make_inputs(name)
        data.to_csv(out / f'input_{name}.csv', index=False)
        base, bm = solve_dispatch(data, 'fixed_time')
        opt, om = solve_dispatch(data, 'optimized')
        for mode, d, m in [('fixed_time', base, bm), ('optimized', opt, om)]:
            m['scenario'] = name
            d.to_csv(out / f'{name}_{mode}.csv', index=False)
            summaries.append(m)
        same_service = (abs(bm['unserved_fixed_mwh'] - om['unserved_fixed_mwh']) < 1e-5
                        and abs(bm['uncompleted_flex_mwh'] - om['uncompleted_flex_mwh']) < 1e-5)
        if same_service:
            assert om['dispatch_cost_yuan'] <= bm['dispatch_cost_yuan'] + 1e-3
        comp = {'scenario': name, 'same_service': same_service,
                'cost_reduction_yuan': bm['dispatch_cost_yuan'] - om['dispatch_cost_yuan'] if same_service else None,
                'cost_reduction_pct': 100 * (1 - om['dispatch_cost_yuan'] / bm['dispatch_cost_yuan']) if same_service else None,
                'curtailment_change_mwh': om['curtailment_mwh'] - bm['curtailment_mwh'],
                'throughput_reduction_mwh': bm['battery_throughput_mwh'] - om['battery_throughput_mwh']}
        comparisons.append(comp)
        plot_case(name, base, opt, out)
        print(json.dumps({'comparison': comp, 'fixed': bm, 'optimized': om}, ensure_ascii=False), flush=True)
    pd.DataFrame(summaries).to_csv(out / 'summary.csv', index=False)
    (out / 'summary.json').write_text(json.dumps(summaries, indent=2, ensure_ascii=False))
    (out / 'comparison.json').write_text(json.dumps(comparisons, indent=2, ensure_ascii=False))
    # Data exchange only. Creating this file does not run the AC circuit model.
    from scipy.io import savemat
    normal = pd.read_csv(out / 'normal_optimized.csv')
    savemat(out / 'normal_schedule_for_simulink.mat', {
        'time_seconds': normal.hour.to_numpy() * 3600,
        'pv_setpoint_W': normal.pv_mw.to_numpy() * 1e6,
        'pv_setpoint_var': normal.pv_q_mvar.to_numpy() * 1e6,
        'wind_setpoint_W': normal.wind_mw.to_numpy() * 1e6,
        'battery_setpoint_W': normal.battery_mw.to_numpy() * 1e6,
        'battery_setpoint_var': normal.battery_q_mvar.to_numpy() * 1e6,
        'load_W': normal.load_served_mw.to_numpy() * 1e6,
        'soc_start': normal.soc_start.to_numpy(), 'soc_end': normal.soc_end.to_numpy(),
        'dt_seconds': 3600.0,
    })
    print('COMPLETED: 5 scenarios, 10 schedules, all physical checks passed.', flush=True)


if __name__ == '__main__':
    main()

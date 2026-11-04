"""Physical and comparison checks, independent of the plotting code."""
import unittest
import numpy as np
import pandas as pd
from dispatch import SETTINGS, make_inputs, solve_dispatch


def data(pv, wind, fixed):
    n = len(pv)
    return pd.DataFrame({'hour': np.arange(n), 'pv_available_mw': pv,
                         'wind_available_mw': wind, 'fixed_load_mw': fixed,
                         'flex_preferred_mw': np.zeros(n), 'flex_allowed_mw': np.zeros(n)})


class DispatchTests(unittest.TestCase):
    def test_no_free_initial_battery_energy(self):
        d, m = solve_dispatch(data([0, 0], [0, 0], [1, 1]), 'optimized')
        self.assertAlmostEqual(m['unserved_fixed_mwh'], 2.0, places=5)
        self.assertAlmostEqual(d.discharge_mw.sum(), 0.0, places=5)
        self.assertAlmostEqual(m['soc_final'], SETTINGS.soc_initial, places=7)

    def test_storage_round_trip_energy(self):
        d, m = solve_dispatch(data([2, 0], [0, 0], [0, 1]), 'optimized')
        self.assertAlmostEqual(m['unserved_fixed_mwh'], 0.0, places=5)
        self.assertAlmostEqual(m['charge_mwh'], 1 / .96**2, places=5)
        self.assertAlmostEqual(m['discharge_mwh'], 1.0, places=5)
        self.assertAlmostEqual(m['soc_final'], .60, places=7)

    def test_equal_service_comparison(self):
        inp = make_inputs('normal')
        b, bm = solve_dispatch(inp, 'fixed_time')
        o, om = solve_dispatch(inp, 'optimized')
        for m in [bm, om]:
            self.assertLess(m['unserved_fixed_mwh'], 1e-5)
            self.assertLess(m['uncompleted_flex_mwh'], 1e-5)
            self.assertAlmostEqual(m['soc_final'], .60, places=7)
        self.assertLessEqual(om['dispatch_cost_yuan'], bm['dispatch_cost_yuan'] + 1e-4)
        self.assertLess(om['battery_throughput_mwh'], bm['battery_throughput_mwh'])
        # Less storage loss with the same generation and served energy leaves MORE surplus.
        self.assertGreater(om['curtailment_mwh'], bm['curtailment_mwh'])

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):
            solve_dispatch(data([-1], [0], [1]), 'optimized')


if __name__ == '__main__':
    unittest.main()

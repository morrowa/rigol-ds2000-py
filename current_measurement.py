#!/usr/bin/env python3

# Copyright 2021 Andrew Morrow.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np
import pyvisa
import pint
import matplotlib.pyplot as plt

from ds2102a import read_normal, last_x_values, Channel

def _rms(x):
    return np.sqrt(x.dot(x)/x.size)

def quick_connect():
    rm = pyvisa.ResourceManager()
    return rm.open_resource(rm.list_resources()[0])

# the current transformer is 1000:1
# the resistor is 100 ohms
_AMPS_PER_VOLT = 10

def measure_power(scope, ureg, volt_chan=Channel.CH1, amp_chan=Channel.CH2):
    volts = read_normal(scope, source=volt_chan) * ureg.V
    amps = (read_normal(scope, source=amp_chan) * _AMPS_PER_VOLT) * ureg.A
    x_vals = last_x_values(scope)
    return (volts * amps, x_vals)

def draw_figure(scope, volt_chan=Channel.CH1, amp_chan=Channel.CH2, filename="figure.svg", csv_filename="data.csv.gz"):
    ureg = pint.UnitRegistry()
    ureg.setup_matplotlib()

    volts = read_normal(scope, source=volt_chan) * ureg.V
    amps = (read_normal(scope, source=amp_chan) * _AMPS_PER_VOLT) * ureg.A
    x_vals = (last_x_values(scope) // 1000000) * ureg.us

    fig, axs = plt.subplots(3, 1, sharex=True)

    axs[0].plot(x_vals, volts)
    axs[1].plot(x_vals, amps)
    axs[2].plot(x_vals, volts*amps)

    axs[0].set_ylim(bottom=-200, top=200)
    axs[0].locator_params(axis='y', nbins=4)
    axs[0].set_title('Instantaneous Power')
    axs[0].set_ylabel('Volts')

    axs[1].set_ylim(bottom=-0.2, top=0.2)
    axs[1].locator_params(axis='y', nbins=4)
    axs[1].set_ylabel('Amps')

    axs[2].set_ylim(bottom=-7, top=35)
    axs[2].locator_params(axis='y', nbins=6)
    axs[2].set_ylabel('Volt-Amps')

    for a in axs:
        a.grid(axis='y')

    fig.savefig(filename, format='svg')

    rows = np.vstack((x_vals.magnitude, volts.magnitude, amps.magnitude)).transpose()
    np.savetxt(csv_filename, rows, fmt=['%d','%e','%e'], delimiter=',', header='usec,volts,amps')

    irms = _rms(amps)
    vrms = _rms(volts)
    apparent_power = irms * vrms
    avg_real_power = (volts * amps).mean()
    pf = avg_real_power / apparent_power
    print("Irms: {:.4f}".format(irms))
    print("Vrms: {:.2f}".format(vrms))
    print("Apparent power: {:.4f}".format(apparent_power))
    print("Avg real power: {:.4f}".format(avg_real_power))
    print("Power factor: {:.4f}".format(pf.magnitude))

if __name__ == "__main__":
    rig = quick_connect()
    draw_figure(rig)


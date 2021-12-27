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
import time
from enum import Enum

_PSEC_PER_SEC = pow(10, 12)

# sample rate of my scope is 2GS/s, so each sample lasts at least 2G^-1 s
# that's 0.5 nanoseconds, or 500 picoseconds
# thus the x axis could be in picoseconds as signed 64b integers

# returns an integer number of picoseconds
def _parse_time(s):
    (man, _, exp) = s.partition('e')
    exp = int(exp)
    (intg, _, frac) = man.partition('.')
    intg = int(intg) * _PSEC_PER_SEC
    frac_digits = len(frac)
    frac = int(frac)
    if intg < 0:
        frac *= -1
    intg += frac * pow(10, 11 - (frac_digits - 1))
    if exp > 0:
        intg *= pow(10, exp)
    elif exp < 0:
        intg //= pow(10, abs(exp))
    return intg

class Channel(Enum):
    CH1 = 'CHAN1'
    CH2 = 'CHAN2'
    MATH = 'MATH'
    FFT = 'FFT'

class _Preamble:
    def __init__(self, s):
        elems = s.split(',')
        self.points = int(elems[2])
        self.count = int(elems[3])
        self.x_inc_str = elems[4]
        self.x_inc = float(elems[4])
        self.x_orig_str = elems[5]
        self.x_orig = float(elems[5])
        self.y_inc = float(elems[7])
        self.y_orig = int(elems[8])
        self.y_ref = int(elems[9])

    def normalize(self, raw_y):
        yvals = raw_y.astype(np.float64)
        yvals -= (self.y_orig + self.y_ref)
        yvals *= self.y_inc
        return yvals

    def x_values(self):
        origin = _parse_time(self.x_orig_str)
        step   = _parse_time(self.x_inc_str)
        stop = origin + step * self.points
        return np.arange(origin, stop, step)

def read_normal(rigol, source=Channel.CH1):
    rigol.write(':WAV:SOUR {}'.format(source.value))
    rigol.write(':WAV:MODE NORM')
    rigol.write(':WAV:FORM BYTE')
    preamble = _Preamble(rigol.query(':WAV:PRE?'))
    raw_values = rigol.query_binary_values(':WAV:DATA?', datatype='B', container=np.array)
    return preamble.normalize(raw_values)

def stop_and_read_raw(rigol, source=Channel.CH1):
    rigol.write(':STOP')
    n_pts = rigol.query_ascii_values(':ACQ:MDEP?', converter='d')[0]
    # print("Expecing {} points.".format(mem_dep))
    rigol.write(':WAV:SOUR {}'.format(source.value))
    rigol.write(':WAV:MODE RAW')
    rigol.write(':WAV:FORM BYTE')
    rigol.write(':WAV:STAR 1')
    rigol.write(':WAV:STOP {}'.format(n_pts))
    rigol.write(':WAV:RES')
    preamble = _Preamble(rigol.query(':WAV:PRE?'))
    rigol.write(':WAV:BEG')
    chunks = list()
    while True:
        status = rigol.query(':WAV:STAT?')
        is_done = status.startswith('IDLE')
        points_ready = int(status[5:])
        if points_ready == 0:
            print("No points ready, sleeping...")
            time.sleep(3)
            continue
        print("Reading {} points".format(points_ready))
        chunks.append(rigol.query_binary_values(':WAV:DATA?', datatype='B', container=np.array))
        if is_done:
            break
        print("Sleeping...")
        time.sleep(2)
    rigol.write(':WAV:END')
    return preamble.normalize(np.concatenate(chunks))

def last_x_values(rigol):
    return _Preamble(rigol.query(':WAV:PRE?')).x_values()


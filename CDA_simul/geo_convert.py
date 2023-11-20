# Copyright 2023 ETRI. 
# License-identifier:GNU General Public License v3.0 or later
# kwmin92@etri.re.kr, yssong00@etri.re.kr

# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU General Public License as published 
# by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with this program. 
# If not, see <https://www.gnu.org/licenses/>.

"""
geo_convert util function
"""
import sys
from math import *
import ast
import struct

def wgs842tm(dLat_deg, dLon_deg):
    """ location change wgs84 -> tm """

    if dLat_deg == "POS-X":
        phi = 36.1231231 / 180. * pi
        ramda = 127.1231231 / 180. * pi

        T = pow(tan(phi), 2)
        T2 = T * T
        C = e2 / (1 - e2) * pow(cos(phi), 2)
        C2 = C * C
        A = (ramda - ramda0) * cos(phi)
        A2 = A * A
        A3 = A * A * A
        A4 = A2 * A2
        A5 = A2 * A3
        A6 = A3 * A3
        N = a / sqrt(1 - e2 * pow(sin(phi), 2))
        M = a * (m0 * phi - m1 * sin(phi * 2) + m2 * sin(phi * 4) - m3 * sin(phi * 6))

        dEast_m = DeltaY + k0 * N * (A + A3 / 6 * (1 - T + C) + A5 / 120 * (5 - 18 * T + T2 + 72 * C - 58 * ep2))
        dNorth_m = DeltaX + k0 * (M - M0 + N * tan(phi) * (
                    A2 / 2 + A4 / 24 * (5 - T + 9 * C + 4 * C2) + A6 / 720 * (61 - 58 * T + T2 + 600 * C - 330 * ep2)))

        return dEast_m, dNorth_m
    elif float(dLat_deg) <= 5:
        dLat_deg = (float(dLat_deg) *50) +232804
        dLon_deg = (float(dLon_deg)+1.02+0.69)*50 +420248
        return dLat_deg, dLon_deg

    elif 35.0 <= float(dLat_deg) <= 38.0:
        phi = float(dLat_deg) / 180. * pi
        ramda = float(dLon_deg) / 180. * pi

        T = pow(tan(phi), 2)
        T2 = T * T
        C = e2 / (1 - e2) * pow(cos(phi), 2) ## 여기 다름
        C2 = C * C
        A = (ramda - ramda0) * cos(phi)
        A2 = A * A
        A3 = A * A * A
        A4 = A2 * A2
        A5 = A2 * A3
        A6 = A3 * A3
        N = a / sqrt(1 - e2 * pow(sin(phi), 2))
        M = a * (m0 * phi - m1 * sin(phi * 2) + m2 * sin(phi * 4) - m3 * sin(phi * 6))

        dEast_m = DeltaY + k0 * N * (A + A3 / 6 * (1 - T + C) + A5 / 120 * (5 - 18 * T + T2 + 72 * C - 58 * ep2))
        dNorth_m = DeltaX + k0 * (M - M0 + N * tan(phi) * (A2 / 2 + A4 / 24 * (5 - T + 9 * C + 4 * C2) 
                                                           + A6 / 720 * (61 - 58 * T + T2 + 600 * C - 330 * ep2)))

        return dEast_m, dNorth_m
    elif 38 < float(dLat_deg) < 300000:
        return dLat_deg, dLon_deg
    elif 300000< float(dLat_deg):
        dLat_deg = str(dLat_deg)[:2] + '.' + str(dLat_deg)[2:]
        dLon_deg = str(dLon_deg)[:3] + '.' + str(dLon_deg)[3:]


        phi = float(dLat_deg) / 180. * pi
        ramda = float(dLon_deg) / 180. * pi

        T = pow(tan(phi), 2)
        T2 = T * T
        C = e2 / (1 - e2) * pow(cos(phi), 2)
        C2 = C * C
        A = (ramda - ramda0) * cos(phi)
        A2 = A * A
        A3 = A * A * A
        A4 = A2 * A2
        A5 = A2 * A3
        A6 = A3 * A3
        N = a / sqrt(1 - e2 * pow(sin(phi), 2))
        M = a * (m0 * phi - m1 * sin(phi * 2) + m2 * sin(phi * 4) - m3 * sin(phi * 6))

        dEast_m = DeltaY + k0 * N * (A + A3 / 6 * (1 - T + C) + A5 / 120 * (5 - 18 * T + T2 + 72 * C - 58 * ep2))
        dNorth_m = DeltaX + k0 * (M - M0 + N * tan(phi) * (
                    A2 / 2 + A4 / 24 * (5 - T + 9 * C + 4 * C2) + A6 / 720 * (61 - 58 * T + T2 + 600 * C - 330 * ep2)))

        return dEast_m, dNorth_m

def tm2wgs84(dEast_m, dNorth_m):
    """ location change tm -> wgs84 """
    M = M0 + (dNorth_m - DeltaX / k0)
    mu1 = M / (a * (1 - e2 / 4. - 3. * e4 / 64. - 5. * e6 / 256.))
    phi1 = mu1 + (3. * e1 / 2. - 27. * e13 / 32.) * sin(2. * mu1) 
    + (21. * e12 / 16. - 55. * e14 / 32.) * sin(4. * mu1) + (151. * e13 / 96.) * sin(6. * mu1) 
    + (1097. * e14 / 512.) * sin(8. * mu1)
    R1 = a * (1. - e2) / (1. - e2 * pow(sin(phi1), 3. / 2.))
    C1 = ep2 * pow(cos(phi1), 2)
    C12 = C1 * C1
    T1 = pow(tan(phi1), 2)
    T12 = T1 * T1
    N1 = a / sqrt(1. - e2 * pow(sin(phi1), 2))
    D = (dEast_m - DeltaY) / (N1 * k0)
    D2 = D * D
    D3 = D2 * D
    D4 = D2 * D2
    D5 = D3 * D2
    D6 = D4 * D2

    phi = phi1 - N1 * tan(phi1) / R1 * (D2 / 2. - D4 / 24. * (5. + 3. * T1 + 10. * C1 - 4. * C12 - 9. * ep2)
          + D6 / 720. * (61. + 90. * T1 + 298. * C1 + 45. * T12 - 252. * ep2 - 3. * C12))
    ramda = ramda0 + 1. / cos(phi1) * (D - D3 / 6. * (1. + 2. * T1 + C1)
                                       + D5 / 120. * (5. - 2. * C1 + 28. * T1 - 3. * C12 + 8. * ep2 + 24. * T12))
    dLon_deg = phi * 180. / pi
    dLat_deg = ramda * 180. / pi

    return dLon_deg, dLat_deg


# 중부원점
phi0 = 38 * pi / 180
ramda0 = 127 * pi / 180

# WGS84
a = 6378137
a2 = a * a
f = 1 / 298.257223563
DeltaY = 200000
DeltaX = 600000
b = a * (1 - f)
b2 = b * b
k0 = 1

# 제 2 이심률
e2 = (a2 - b2) / a2
e4 = e2 * e2
e6 = e2 * e2 * e2
e1 = (1 - sqrt(1 - e2)) / (1 + sqrt(1 - e2))
e12 = e1 * e1
e13 = e1 * e1 * e1
e14 = (e1 * e1) * (e1 * e1)

# 제 1 이심률
ep2 = (a2 - b2) / b2

#자오선호장

m0 = (1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256)
m1 = (3 * e2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024)
m2 = (15 * e4 / 256 + 45 * e6 / 1024)
m3 = 35 * e6 / 3072
M0 = a * (m0 * phi0 - m1 * sin(2 * phi0) + m2 * sin(4 * phi0) - m3 * sin(6 * phi0)) # 투영원점 자오선호장

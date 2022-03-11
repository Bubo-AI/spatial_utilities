#!/usr/bin/env python3

"""
Convert British National Grid References to Easting and Northing coordinates.

Prints the Easting and Northing coordinates of the provided grid reference. Prints south
west point coordinates of reference box by default. You can specify the point of the box
to print by passing the point as the second argument. Accepted values are: "SW", "NW",
"NE", "SE", "MID", "SWNE".

Disclaimer: Adapted to Python from the original Perl code by Ben Soares for EDINA
national datacentre. For original implementation, please refer to:
https://digimap.edina.ac.uk/help/files/resource-hub/downloads/ngconv.pl

Example: python bng2en.py NZ20NE SW

"""

# Copyright (c) 2022 Bubo.AI

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Tuple, Union
import re
import sys

__version__ = "0.1.0"
__author__ = "Furkan Tektas, Ben Soares"
__copyright__ = "Copyright 2022, Bubo.AI"
__license__ = "MIT"
__credits__ = ["EDINA national datacentre"]


def bng2en(
    grid_ref: str, point: str = "SW"
) -> Union[Tuple[str, str], Tuple[str, str, str, str]]:
    """Convert British National Grid References to Easting and Northing coordinates.
    Adapted to Python from the original Perl code by Ben Soares for EDINA national
    datacentre.
    Reference: https://digimap.edina.ac.uk/help/files/resource-hub/downloads/ngconv.pl


    Args:
        grid_ref (str): National Grid Reference
        point (str, optional): Convert to specified point(s) on box. Accepted values are
        "SW", "NW", "NE", "SE", "MID", or "SWNE". Defaults to "SW".

    Returns:
        Union[Tuple[str,str], Tuple[str,str,str,str]]: Easting and Northing coordinates
        if point is not SWNE, otherwise South, West, North, East coordinates.
    """

    assert point in ["SW", "NW", "NE", "SE", "MID", "SWNE"], "Invalid point"
    matches = re.match(
        r"^([A-Z])([A-Z])\s*((\d{2}){0,5})\s*([NS])?([EW])?$", grid_ref.upper()
    )

    assert matches, "Invalid grid reference"
    l1, l2, d, _, q1, q2 = matches.groups()

    digits = 5
    d_length = len(d) // 2
    if d:
        dx = int(d[:d_length]) * 10 ** (digits - d_length)
        dy = int(d[d_length:]) * 10 ** (digits - d_length)
    else:
        dx = 0
        dy = 0
    grid1 = ((ord(l1) - 1) if (ord(l1) > ord("I")) else ord(l1)) - ord("A")
    grid2 = ((ord(l2) - 1) if (ord(l2) > ord("I")) else ord(l2)) - ord("A")

    grid1_x = grid1 % 5
    grid1_y = 4 - grid1 // 5

    grid2_x = grid2 % 5
    grid2_y = 4 - grid2 // 5

    # put SV as origin
    grid1_x -= 2
    grid1_y -= 1

    precision = 10 ** (digits - d_length)

    quadrant_x = 1 if (q2 == "E") else 0
    quadrant_y = 1 if (q1 == "N") else 0

    if q1 and q2:
        precision //= 2

    easting = (grid1_x * 500_000) + (grid2_x * 100_000) + dx + (quadrant_x * precision)
    northing = (grid1_y * 500_000) + (grid2_y * 100_000) + dy + (quadrant_y * precision)

    if point == "SW":
        return (easting, northing)
    elif point == "NW":
        return (easting, northing + precision)
    elif point == "SE":
        return (easting + precision, northing)
    elif point == "NE":
        return (easting + precision, northing + precision)
    elif point == "MID":
        return (easting + (precision // 2), northing + (precision // 2))
    elif point == "SWNE":
        return (easting, northing, easting + precision, northing + precision)
    else:
        raise ValueError("Invalid point value")


def main() -> None:
    assert 2 <= len(sys.argv) <= 3, "Usage: bng2en.py <grid_ref> [point]"
    grid_ref = sys.argv[1].strip().upper()
    point = sys.argv[2].strip().upper() if len(sys.argv) == 3 else "SW"
    coordinates = bng2en(grid_ref=grid_ref, point=point)
    formatted_coordinates = ", ".join(map(str, coordinates))  # seperate by comma
    print(formatted_coordinates)


if __name__ == "__main__":
    main()

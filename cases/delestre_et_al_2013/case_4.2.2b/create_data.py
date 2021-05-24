#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020-2021 Pi-Yueh Chuang <pychuang@gwu.edu>
#
# Distributed under terms of the BSD 3-Clause license.

"""Create topography and I.C. file for case 4.2.2-2 in Delestre et al., 2013.

Note, the elevation data in the resulting NetCDF file is defined at vertices,
instead of cell centers. But the I.C. is defined at cell centers.
"""
import pathlib
import yaml
import numpy
from torchswe.utils.data import get_empty_whuhvmodel, get_gridlines
from torchswe.utils.io import create_soln_snapshot_file, create_topography_file


def topo(x, y, h0=0.1, L=4., a=1.):
    """Topography."""
    # pylint: disable=invalid-name

    r = numpy.sqrt((x-L/2.)**2+(y-L/2.)**2)
    return - h0 * (1. - (r / a)**2)


def exact_soln(x, y, t, g=9.81, h0=0.1, L=4., a=1., eta=0.5):
    """Exact solution."""
    # pylint: disable=invalid-name, too-many-arguments

    omega = numpy.sqrt(2.*h0*g) / a
    z = topo(x, y, h0, L, a)
    cot = numpy.cos(omega*t)
    sot = numpy.sin(omega*t)

    h = eta * h0 * (2 * (x - L / 2) * cot + 2 * (y - L / 2.) * sot - eta) / (a * a) - z
    h[h < 0.] = 0.

    return h + z, - h * eta * omega * sot, h * eta * omega * cot


def main():
    """Main function"""
    # pylint: disable=invalid-name

    case = pathlib.Path(__file__).expanduser().resolve().parent

    with open(case.joinpath("config.yaml"), 'r') as f:
        config: Config = yaml.load(f, Loader=yaml.Loader)

    # gridlines; ignore temporal axis
    grid = get_gridlines(*config.spatial.discretization, *config.spatial.domain, [], config.dtype)

    # topography, defined on cell vertices
    create_topography_file(
        case.joinpath(config.topo.file), [grid.x.vert, grid.y.vert],
        topo(*numpy.meshgrid(grid.x.vert, grid.y.vert)))

    # initial conditions, defined on cell centers
    ic = get_empty_whuhvmodel(*config.spatial.discretization, config.dtype)
    ic.w, ic.hu, ic.hv = exact_soln(*numpy.meshgrid(grid.x.cntr, grid.y.cntr), 0.)
    ic.check()
    create_soln_snapshot_file(case.joinpath(config.ic.file), grid, ic)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())

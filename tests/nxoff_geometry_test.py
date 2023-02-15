import h5py
import numpy as np
import pytest
import scipp as sc

from scippnexus import NXentry, NXoff_geometry, NXroot
from scippnexus.nxoff_geometry import off_to_shape


@pytest.fixture()
def nxroot(request):
    """Yield NXroot containing a single NXentry named 'entry'"""
    with h5py.File('dummy.nxs', mode='w', driver="core", backing_store=False) as f:
        root = NXroot(f)
        root.create_class('entry', NXentry)
        yield root


def test_vertices_loaded_as_vector3(nxroot):
    shape = nxroot['entry'].create_class('shape', NXoff_geometry)
    values = [[1, 2, 3], [4, 5, 6]]
    shape['vertices'] = sc.array(dims=['ignored', 'comp'], values=values, unit='mm')
    loaded = shape[()]
    assert sc.identical(loaded['vertices'],
                        sc.vectors(dims=['vertex'], values=values, unit='mm'))


def test_field_properties(nxroot):
    shape = nxroot['entry'].create_class('shape', NXoff_geometry)
    values = [[1, 2, 3], [4, 5, 6]]
    shape['vertices'] = sc.array(dims=['ignored', 'comp'], values=values, unit='m')
    shape['winding_order'] = sc.array(dims=['ignored'], values=[], unit=None)
    shape['faces'] = sc.array(dims=['ignored'], values=[], unit=None)
    loaded = shape[()]
    assert loaded['vertices'].dims == ('vertex', )
    assert loaded['winding_order'].dims == ('winding_order', )
    assert loaded['winding_order'].unit is None
    assert loaded['faces'].dims == ('face', )
    assert loaded['faces'].unit is None


def test_off_to_shape_without_detector_faces_yields_scalar_shape_with_all_faces(nxroot):
    off = nxroot['entry'].create_class('off', NXoff_geometry)
    values = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    off['vertices'] = sc.array(dims=['_', 'comp'], values=values, unit='m')
    off['winding_order'] = sc.array(dims=['_'], values=[0, 1, 2, 0, 2, 1], unit=None)
    off['faces'] = sc.array(dims=['_'], values=[0, 3], unit=None)
    loaded = off[()]
    shape = off_to_shape(**loaded)
    assert shape.ndim == 0
    assert sc.identical(shape.bins.size(), sc.index(2))


def test_off_to_shape_with_single_detector_yields_1d_shape(nxroot):
    off = nxroot['entry'].create_class('off', NXoff_geometry)
    values = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    off['vertices'] = sc.array(dims=['_', 'comp'], values=values, unit='m')
    off['winding_order'] = sc.array(dims=['_'], values=[0, 1, 2, 0, 2, 1], unit=None)
    off['faces'] = sc.array(dims=['_'], values=[0, 3], unit=None)
    det_num1 = 7
    off['detector_faces'] = sc.array(dims=['_', 'dummy'],
                                     values=[[0, det_num1], [1, det_num1]],
                                     unit=None)
    loaded = off[()]
    shape = off_to_shape(**loaded)
    assert shape.sizes == {'detector_number': 1}
    assert sc.identical(
        shape.coords['detector_number'],
        sc.array(dims=['detector_number'], values=[det_num1], unit=None))
    assert sc.identical(shape.bins.size().data,
                        sc.array(dims=['detector_number'], values=[2], unit=None))


def test_off_to_shape_with_two_detectors_yields_1d_shape(nxroot):
    off = nxroot['entry'].create_class('off', NXoff_geometry)
    values = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    off['vertices'] = sc.array(dims=['_', 'comp'], values=values, unit='m')
    off['winding_order'] = sc.array(dims=['_'], values=[0, 1, 2, 0, 2, 1], unit=None)
    off['faces'] = sc.array(dims=['_'], values=[0, 3], unit=None)
    det_num1 = 1
    det_num2 = 3
    off['detector_faces'] = sc.array(dims=['_', 'dummy'],
                                     values=[[0, det_num2], [1, det_num1]],
                                     unit=None)
    loaded = off[()]
    shape = off_to_shape(**loaded)
    assert shape.sizes == {'detector_number': 2}
    assert sc.identical(shape.bins.size().data,
                        sc.array(dims=['detector_number'], values=[1, 1], unit=None))
    assert sc.identical(
        shape.coords['detector_number'],
        sc.array(dims=['detector_number'], values=[det_num1, det_num2], unit=None))
    assert sc.identical(
        shape[0].value,
        sc.vectors(dims=['face', 'vertex'], values=[values[[0, 2, 1]]], unit='m'))
    assert sc.identical(shape[1].value,
                        sc.vectors(dims=['face', 'vertex'], values=[values], unit='m'))

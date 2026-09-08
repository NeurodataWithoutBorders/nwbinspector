from datetime import datetime
from unittest import TestCase
from uuid import uuid4

import numpy as np
from hdmf.common.table import DynamicTable, DynamicTableRegion
from pynwb import NWBFile
from pynwb.device import Device, DeviceModel
from pynwb.file import Subject
from pynwb.image import ImageSeries
from pynwb.ophys import (
    ImageSegmentation,
    ImagingPlane,
    OpticalChannel,
    PlaneSegmentation,
    RoiResponseSeries,
    TwoPhotonSeries,
)

from nwbinspector import Importance, InspectorMessage
from nwbinspector.checks import (
    check_emission_lambda_in_nm,
    check_excitation_lambda_in_nm,
    check_image_series_data_size,  # Technically an ImageSeries check, but test is more convenient here
    check_imaging_plane_location_allen_ccf,
    check_photon_series_undeclared_depth,
    check_plane_segmentation_image_mask_shape_against_ref_images,
    check_roi_response_series_dims,
    check_roi_response_series_link_to_plane_segmentation,
)


class TestCheckRoiResponseSeries(TestCase):
    def setUp(self):
        nwbfile = NWBFile(
            session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone()
        )

        device_model = nwbfile.create_device_model(
            name="My Microscope",
            description="My two-photon microscope",
            manufacturer="The best microscope manufacturer",
        )
        device = nwbfile.create_device(name="Microscope", description="My two-photon microscope", model=device_model)
        optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
        imaging_plane = nwbfile.create_imaging_plane(
            name="ImagingPlane",
            optical_channel=optical_channel,
            imaging_rate=30.0,
            description="a very interesting part of the brain",
            device=device,
            excitation_lambda=600.0,
            indicator="GFP",
            location="V1",
            grid_spacing=[0.01, 0.01],
            grid_spacing_unit="meters",
            origin_coords=[1.0, 2.0, 3.0],
            origin_coords_unit="meters",
        )

        img_seg = ImageSegmentation()

        self.plane_segmentation = img_seg.create_plane_segmentation(
            name="PlaneSegmentation",
            description="output from segmenting my favorite imaging plane",
            imaging_plane=imaging_plane,
        )

        self.ophys_module = nwbfile.create_processing_module(
            name="ophys",
            description="optical physiology processed data",
        )

        self.ophys_module.add(img_seg)

        for _ in range(10):
            image_mask = np.zeros((100, 100))
            self.plane_segmentation.add_roi(image_mask=image_mask)
        self.nwbfile = nwbfile

    def test_check_flipped_dims(self):
        rt_region = self.plane_segmentation.create_roi_table_region(
            region=[0, 1, 2, 3, 4],
            description="the first of two ROIs",
        )

        roi_resp_series = RoiResponseSeries(
            name="RoiResponseSeries",
            data=np.ones((5, 40)),  # 50 samples, 2 ROIs
            rois=rt_region,
            unit="n.a.",
            rate=30.0,
        )

        self.ophys_module.add(roi_resp_series)

        assert check_roi_response_series_dims(roi_resp_series) == InspectorMessage(
            message=(
                "The second dimension of data does not match the length of rois, "
                "but instead the first does. Data is oriented incorrectly and should be transposed."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_roi_response_series_dims",
            object_type="RoiResponseSeries",
            object_name="RoiResponseSeries",
        )

    def test_check_wrong_dims(self):
        rt_region = self.plane_segmentation.create_roi_table_region(
            region=[0, 1, 2, 3, 4],
            description="the first of two ROIs",
        )

        roi_resp_series = RoiResponseSeries(
            name="RoiResponseSeries",
            data=np.ones((10, 40)),  # 50 samples, 2 ROIs
            rois=rt_region,
            unit="n.a.",
            rate=30.0,
        )

        self.ophys_module.add(roi_resp_series)

        assert check_roi_response_series_dims(roi_resp_series) == InspectorMessage(
            message="The second dimension of data does not match the length of rois. Your " "data may be transposed.",
            importance=Importance.CRITICAL,
            check_function_name="check_roi_response_series_dims",
            object_type="RoiResponseSeries",
            object_name="RoiResponseSeries",
        )

    def test_pass_check_roi_response_series_dims(self):
        rt_region = self.plane_segmentation.create_roi_table_region(
            region=[0, 1, 2, 3, 4],
            description="the first of two ROIs",
        )

        roi_resp_series = RoiResponseSeries(
            name="RoiResponseSeries",
            data=np.ones((40, 5)),  # 50 samples, 2 ROIs
            rois=rt_region,
            unit="n.a.",
            rate=30.0,
        )

        assert check_roi_response_series_dims(roi_resp_series) is None

    def test_check_roi_response_series_link_to_plane_segmentation(self):
        dt = DynamicTable(name="name", description="desc")
        dt.add_column("a", "desc")
        for _ in range(5):
            dt.add_row(a=1)
        dtr = DynamicTableRegion(name="n", description="desc", data=[0, 1, 2, 3, 4], table=dt)
        roi_resp_series = RoiResponseSeries(
            name="RoiResponseSeries",
            data=np.ones((40, 5)),  # 50 samples, 2 ROIs
            rois=dtr,
            unit="n.a.",
            rate=30.0,
        )

        self.ophys_module.add(roi_resp_series)

        assert check_roi_response_series_link_to_plane_segmentation(roi_resp_series) == InspectorMessage(
            message="rois field does not point to a PlaneSegmentation table.",
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_roi_response_series_link_to_plane_segmentation",
            object_type="RoiResponseSeries",
            object_name="RoiResponseSeries",
        )

    def test_pass_check_roi_response_series_link_to_plane_segmentation(self):
        rt_region = self.plane_segmentation.create_roi_table_region(
            region=[0, 1, 2, 3, 4],
            description="the first of two ROIs",
        )

        roi_resp_series = RoiResponseSeries(
            name="RoiResponseSeries",
            data=np.ones((40, 5)),  # 50 samples, 2 ROIs
            rois=rt_region,
            unit="n.a.",
            rate=30.0,
        )

        assert check_roi_response_series_link_to_plane_segmentation(roi_resp_series) is None


def test_check_excitation_lambda_in_nm():
    device_model = DeviceModel(
        name="My Microscope", description="My two-photon microscope", manufacturer="The best microscope manufacturer"
    )
    device = Device(name="Microscope", description="My two-photon microscope", model=device_model)
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
    imaging_plane = ImagingPlane(
        name="ImagingPlane",
        optical_channel=optical_channel,
        imaging_rate=30.0,
        description="a very interesting part of the brain",
        device=device,
        excitation_lambda=1.0,
        indicator="GFP",
        location="V1",
        grid_spacing=[0.01, 0.01],
        grid_spacing_unit="meters",
        origin_coords=[1.0, 2.0, 3.0],
        origin_coords_unit="meters",
    )

    assert check_excitation_lambda_in_nm(imaging_plane).message == "excitation lambda of 1.0 should be in units of nm."


def test_pass_check_excitation_lambda_in_nm():
    device_model = DeviceModel(
        name="My Microscope", description="My two-photon microscope", manufacturer="The best microscope manufacturer"
    )
    device = Device(name="Microscope", description="My two-photon microscope", model=device_model)
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
    imaging_plane = ImagingPlane(
        name="ImagingPlane",
        optical_channel=optical_channel,
        imaging_rate=30.0,
        description="a very interesting part of the brain",
        device=device,
        excitation_lambda=300.0,
        indicator="GFP",
        location="V1",
        grid_spacing=[0.01, 0.01],
        grid_spacing_unit="meters",
        origin_coords=[1.0, 2.0, 3.0],
        origin_coords_unit="meters",
    )

    assert check_excitation_lambda_in_nm(imaging_plane) is None


def test_check_emission_lambda_in_nm():
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=5.0)
    assert check_emission_lambda_in_nm(optical_channel).message == "emission lambda of 5.0 should be in units of nm."


def test_pass_check_emission_lambda_in_nm():
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
    assert check_emission_lambda_in_nm(optical_channel) is None


def test_pass_check_plane_segmentation_image_mask_dims_against_imageseries():
    device_model = DeviceModel(
        name="My Microscope", description="My two-photon microscope", manufacturer="The best microscope manufacturer"
    )
    device = Device(name="Microscope", description="My two-photon microscope", model=device_model)
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
    imaging_plane = ImagingPlane(
        name="ImagingPlane",
        optical_channel=optical_channel,
        imaging_rate=30.0,
        description="a very interesting part of the brain",
        device=device,
        excitation_lambda=300.0,
        indicator="GFP",
        location="V1",
        grid_spacing=[0.01, 0.01],
        grid_spacing_unit="meters",
        origin_coords=[1.0, 2.0, 3.0],
        origin_coords_unit="meters",
    )

    two_photon_series = TwoPhotonSeries(
        name="TwoPhotonSeries",
        imaging_plane=imaging_plane,
        data=np.ones((20, 10, 10)),
        unit="n.a.",
        rate=30.0,
    )

    plane_segmentation = PlaneSegmentation(
        description="my plane segmentation",
        imaging_plane=imaging_plane,
        reference_images=two_photon_series,
    )

    plane_segmentation.add_roi(image_mask=np.ones((10, 10)))

    assert check_plane_segmentation_image_mask_shape_against_ref_images(plane_segmentation) is None


def test_fail_check_plane_segmentation_image_mask_dims_against_imageseries():
    device_model = DeviceModel(
        name="My Microscope", description="My two-photon microscope", manufacturer="The best microscope manufacturer"
    )
    device = Device(name="Microscope", description="My two-photon microscope", model=device_model)
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
    imaging_plane = ImagingPlane(
        name="ImagingPlane",
        optical_channel=optical_channel,
        imaging_rate=30.0,
        description="a very interesting part of the brain",
        device=device,
        excitation_lambda=300.0,
        indicator="GFP",
        location="V1",
        grid_spacing=[0.01, 0.01],
        grid_spacing_unit="meters",
        origin_coords=[1.0, 2.0, 3.0],
        origin_coords_unit="meters",
    )

    two_photon_series = TwoPhotonSeries(
        name="TwoPhotonSeries",
        imaging_plane=imaging_plane,
        data=np.ones((20, 10, 10)),
        unit="n.a.",
        rate=30.0,
    )

    plane_segmentation = PlaneSegmentation(
        description="my plane segmentation",
        imaging_plane=imaging_plane,
        reference_images=two_photon_series,
    )

    plane_segmentation.add_roi(image_mask=np.ones((9, 10)))

    assert check_plane_segmentation_image_mask_shape_against_ref_images(plane_segmentation) == [
        InspectorMessage(
            message="image_mask of shape (9, 10) does not match reference image TwoPhotonSeries with shape (10, 10).",
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_plane_segmentation_image_mask_shape_against_ref_images",
            object_type="PlaneSegmentation",
            object_name="ImagingPlane",
            location="/",
        )
    ]


def test_false_positive_skip_check_image_series_data_size():
    device_model = DeviceModel(
        name="My Microscope", description="My two-photon microscope", manufacturer="The best microscope manufacturer"
    )
    device = Device(name="Microscope", description="My two-photon microscope", model=device_model)
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
    imaging_plane = ImagingPlane(
        name="ImagingPlane",
        optical_channel=optical_channel,
        imaging_rate=30.0,
        description="a very interesting part of the brain",
        device=device,
        excitation_lambda=300.0,
        indicator="GFP",
        location="V1",
        grid_spacing=[0.01, 0.01],
        grid_spacing_unit="meters",
        origin_coords=[1.0, 2.0, 3.0],
        origin_coords_unit="meters",
    )

    two_photon_series = TwoPhotonSeries(
        name="TwoPhotonSeries",
        imaging_plane=imaging_plane,
        data=np.empty(
            shape=(110 * 10**6, 1, 1), dtype="uint8"
        ),  # Empty data, but of shape+dtype that would be more than default GB threshold
        unit="n.a.",
        rate=30.0,
    )

    assert check_image_series_data_size(image_series=two_photon_series, gb_lower_bound=0.1) is None


def _make_nwbfile_with_imaging_plane(location, species=None):
    """Helper to create an NWBFile with an ImagingPlane at the given location."""
    nwbfile = NWBFile(
        session_description="test",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
    )
    if species is not None:
        nwbfile.subject = Subject(subject_id="001", species=species)
    device = nwbfile.create_device(name="Microscope")
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
    imaging_plane = nwbfile.create_imaging_plane(
        name="ImagingPlane",
        optical_channel=optical_channel,
        imaging_rate=30.0,
        description="a very interesting part of the brain",
        device=device,
        excitation_lambda=600.0,
        indicator="GFP",
        location=location,
    )
    return imaging_plane


def test_pass_check_imaging_plane_location_allen_ccf_acronym():
    imaging_plane = _make_nwbfile_with_imaging_plane(location="VISp", species="Mus musculus")
    assert check_imaging_plane_location_allen_ccf(imaging_plane) is None


def test_pass_check_imaging_plane_location_allen_ccf_full_name():
    imaging_plane = _make_nwbfile_with_imaging_plane(location="Primary visual area", species="Mus musculus")
    assert check_imaging_plane_location_allen_ccf(imaging_plane) is None


def test_fail_check_imaging_plane_location_allen_ccf():
    imaging_plane = _make_nwbfile_with_imaging_plane(location="my_custom_region", species="Mus musculus")
    result = check_imaging_plane_location_allen_ccf(imaging_plane)
    assert result == InspectorMessage(
        message=(
            "ImagingPlane location 'my_custom_region' is not a term in the Allen Mouse Brain CCF ontology. "
            "Please use either the full name or abbreviation from the Allen Mouse Brain Atlas "
            "(e.g., 'Primary visual area' or 'VISp'). This check can be ignored if Allen CCF "
            "terms do not meet your needs."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_imaging_plane_location_allen_ccf",
        object_type="ImagingPlane",
        object_name="ImagingPlane",
    )


def test_skip_check_imaging_plane_location_allen_ccf_non_mouse():
    imaging_plane = _make_nwbfile_with_imaging_plane(location="my_custom_region", species="Homo sapiens")
    assert check_imaging_plane_location_allen_ccf(imaging_plane) is None


def test_skip_check_imaging_plane_location_allen_ccf_no_subject():
    imaging_plane = _make_nwbfile_with_imaging_plane(location="my_custom_region", species=None)
    assert check_imaging_plane_location_allen_ccf(imaging_plane) is None


def _make_imaging_plane(grid_spacing=None, origin_coords=None):
    """Build a standalone ImagingPlane with the requested geometry declarations."""
    device_model = DeviceModel(name="Model", description="microscope model", manufacturer="Manufacturer")
    device = Device(name="Microscope", description="a microscope", model=device_model)
    optical_channel = OpticalChannel(name="OpticalChannel", description="an optical channel", emission_lambda=500.0)
    geometry = {}
    if grid_spacing is not None:
        geometry.update(grid_spacing=grid_spacing, grid_spacing_unit="meters")
    if origin_coords is not None:
        geometry.update(origin_coords=origin_coords, origin_coords_unit="meters")

    return ImagingPlane(
        name="ImagingPlane",
        optical_channel=optical_channel,
        description="an imaging plane",
        device=device,
        excitation_lambda=600.0,
        indicator="GFP",
        location="V1",
        **geometry,
    )


def _make_photon_series(shape, imaging_plane, dimension=None):
    return TwoPhotonSeries(
        name="TwoPhotonSeries",
        imaging_plane=imaging_plane,
        data=np.ones(shape),
        dimension=dimension,
        unit="n.a.",
        rate=30.0,
    )


class TestCheckPhotonSeriesUndeclaredDepth(TestCase):
    def test_undeclared_singleton_depth_triggers(self):
        """The dandiset 000491 shape: 4D with depth 1 and no geometry declared anywhere."""
        imaging_plane = _make_imaging_plane()
        photon_series = _make_photon_series(shape=(20, 10, 10, 1), imaging_plane=imaging_plane)

        assert check_photon_series_undeclared_depth(photon_series) == InspectorMessage(
            message=(
                "The data is four-dimensional with a depth axis of length 1, but neither "
                "the series nor its imaging plane ('ImagingPlane') declares a depth. Set "
                "'grid_spacing' (or 'origin_coords') on the imaging plane to three components, or "
                "'dimension' on the series, so the data can be interpreted as a volume. If the axis is a "
                "leftover from splitting channels or planes, store the data as (time, rows, columns) instead."
            ),
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_photon_series_undeclared_depth",
            object_type="TwoPhotonSeries",
            object_name="TwoPhotonSeries",
            location="/",
        )

    def test_undeclared_real_depth_triggers(self):
        """A depth greater than one is still uninterpretable as a volume without a declared geometry."""
        imaging_plane = _make_imaging_plane()
        photon_series = _make_photon_series(shape=(20, 10, 10, 4), imaging_plane=imaging_plane)

        assert check_photon_series_undeclared_depth(photon_series) is not None

    def test_planar_series_passes(self):
        imaging_plane = _make_imaging_plane()
        photon_series = _make_photon_series(shape=(20, 10, 10), imaging_plane=imaging_plane)

        assert check_photon_series_undeclared_depth(photon_series) is None

    def test_declared_volume_passes(self):
        imaging_plane = _make_imaging_plane(grid_spacing=[0.01, 0.01, 0.02])
        photon_series = _make_photon_series(shape=(20, 10, 10, 4), imaging_plane=imaging_plane)

        assert check_photon_series_undeclared_depth(photon_series) is None

    def test_singleton_depth_declared_by_grid_spacing_passes(self):
        imaging_plane = _make_imaging_plane(grid_spacing=[0.01, 0.01, 0.02])
        photon_series = _make_photon_series(shape=(20, 10, 10, 1), imaging_plane=imaging_plane)

        assert check_photon_series_undeclared_depth(photon_series) is None

    def test_singleton_depth_declared_by_origin_coords_passes(self):
        imaging_plane = _make_imaging_plane(origin_coords=[1.0, 2.0, 3.0])
        photon_series = _make_photon_series(shape=(20, 10, 10, 1), imaging_plane=imaging_plane)

        assert check_photon_series_undeclared_depth(photon_series) is None

    def test_singleton_depth_declared_by_dimension_passes(self):
        imaging_plane = _make_imaging_plane()
        photon_series = _make_photon_series(shape=(20, 10, 10, 1), imaging_plane=imaging_plane, dimension=[10, 10, 1])

        assert check_photon_series_undeclared_depth(photon_series) is None

    def test_two_component_grid_spacing_still_triggers(self):
        """A planar grid_spacing does not declare a depth, so the axis is still undeclared."""
        imaging_plane = _make_imaging_plane(grid_spacing=[0.01, 0.01])
        photon_series = _make_photon_series(shape=(20, 10, 10, 1), imaging_plane=imaging_plane)

        assert check_photon_series_undeclared_depth(photon_series) is not None

    def test_plain_image_series_is_ignored(self):
        """An ImageSeries has no imaging plane, so it has no depth semantics to check."""
        image_series = ImageSeries(name="ImageSeries", data=np.ones((20, 10, 10, 1)), unit="n.a.", rate=30.0)

        assert check_photon_series_undeclared_depth(image_series) is None

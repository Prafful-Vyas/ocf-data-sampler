"""
Site class testing - SiteSample
"""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from ocf_data_sampler.torch_datasets.sample.site import SiteSample


@pytest.fixture
def sample_data():
    """Fixture creation with sample data"""

    #  Time periods specified
    init_time = pd.Timestamp("2023-01-01 00:00")
    target_times = pd.date_range("2023-01-01 00:00", periods=4, freq="1h")
    sat_times = pd.date_range("2023-01-01 00:00", periods=7, freq="5min")
    site_times = pd.date_range("2023-01-01 00:00", periods=4, freq="30min")

    # Defined steps for NWP data
    steps = ((target_times - init_time).total_seconds()).astype(np.int32)

    # Create the sample dataset
    return xr.Dataset(
        data_vars={
            "nwp-ukv": (
                [
                    "nwp-ukv__target_time_utc",
                    "nwp-ukv__channel",
                    "nwp-ukv__y_osgb",
                    "nwp-ukv__x_osgb",
                ],
                np.random.rand(4, 1, 2, 2),
            ),
            "satellite": (
                [
                    "satellite__time_utc",
                    "satellite__channel",
                    "satellite__y_geostationary",
                    "satellite__x_geostationary",
                ],
                np.random.rand(7, 1, 2, 2),
            ),
            "site": (["site__time_utc"], np.random.rand(4)),
        },
        coords={
            # NWP coords
            "nwp-ukv__target_time_utc": target_times,
            "nwp-ukv__channel": ["dswrf"],
            "nwp-ukv__y_osgb": [0, 1],
            "nwp-ukv__x_osgb": [0, 1],
            "nwp-ukv__init_time_utc": init_time,
            "nwp-ukv__step": ("nwp-ukv__target_time_utc", steps),
            # Sat coords
            "satellite__time_utc": sat_times,
            "satellite__channel": ["vis"],
            "satellite__y_geostationary": [0, 1],
            "satellite__x_geostationary": [0, 1],
            # Site coords
            "site__time_utc": site_times,
            "site__capacity_kwp": 1000.0,
            "site__site_id": 1,
            "site__longitude": -3.5,
            "site__latitude": 51.5,
            # Site features as coords
            "site__solar_azimuth": ("site__time_utc", np.random.rand(4)),
            "site__solar_elevation": ("site__time_utc", np.random.rand(4)),
            "site__date_cos": ("site__time_utc", np.random.rand(4)),
            "site__date_sin": ("site__time_utc", np.random.rand(4)),
            "site__time_cos": ("site__time_utc", np.random.rand(4)),
            "site__time_sin": ("site__time_utc", np.random.rand(4)),
        },
    )


def test_site_sample_with_data(sample_data):
    """Testing of defined sample with actual data"""
    sample = SiteSample(sample_data)

    # Assert data structure
    assert isinstance(sample._data, xr.Dataset)

    # Assert dimensions / shapes
    expected_dims = {
        "satellite__x_geostationary",
        "site__time_utc",
        "nwp-ukv__target_time_utc",
        "nwp-ukv__x_osgb",
        "satellite__channel",
        "satellite__y_geostationary",
        "satellite__time_utc",
        "nwp-ukv__channel",
        "nwp-ukv__y_osgb",
    }
    assert set(sample._data.dims) == expected_dims
    assert sample._data["satellite"].values.shape == (7, 1, 2, 2)
    assert sample._data["nwp-ukv"].values.shape == (4, 1, 2, 2)
    assert sample._data["site"].values.shape == (4,)


def test_save_load(tmp_path, sample_data):
    """Save and load functionality"""
    sample = SiteSample(sample_data)
    filepath = tmp_path / "test_sample.nc"
    sample.save(filepath)

    # Assert file exists and has content
    assert filepath.exists()
    assert filepath.stat().st_size > 0

    # Load and verify
    loaded = SiteSample.load(filepath)
    assert isinstance(loaded, SiteSample)
    assert isinstance(loaded._data, xr.Dataset)

    # Compare original / loaded data
    xr.testing.assert_identical(sample._data, loaded._data)


def test_invalid_data_type():
    """Handling of invalid data types"""

    with pytest.raises(TypeError, match="Data must be xarray Dataset"):
        _ = SiteSample({"invalid": "data"})


def test_to_numpy(sample_data):
    """To numpy conversion"""
    sample = SiteSample(sample_data)
    numpy_data = sample.to_numpy()

    # Assert structure
    assert isinstance(numpy_data, dict)
    assert "site" in numpy_data
    assert "nwp" in numpy_data

    # Check site - numpy array instead of dict
    site_data = numpy_data["site"]
    assert isinstance(site_data, np.ndarray)
    assert site_data.ndim == 1
    assert len(site_data) == 4
    assert np.all(site_data >= 0) and np.all(site_data <= 1)

    # Check NWP
    assert "ukv" in numpy_data["nwp"]
    nwp_data = numpy_data["nwp"]["ukv"]
    assert "nwp" in nwp_data
    assert nwp_data["nwp"].shape == (4, 1, 2, 2)


def test_data_consistency(sample_data):
    """Consistency of data across operations"""
    sample = SiteSample(sample_data)
    numpy_data = sample.to_numpy()

    # Assert components remain consistent after conversion above
    assert numpy_data["nwp"]["ukv"]["nwp"].shape == (4, 1, 2, 2)
    assert "site" in numpy_data

    # Update site data checks to expect numpy array
    assert isinstance(numpy_data["site"], np.ndarray)
    assert numpy_data["site"].shape == (4,)
    assert np.all(numpy_data["site"] >= 0)
    assert np.all(numpy_data["site"] <= 1)

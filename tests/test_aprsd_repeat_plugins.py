#!/usr/bin/env python

"""Tests for `aprsd_repeat_plugins` package."""

import unittest

from aprsd import config as aprsd_config

from aprsd_repeat_plugins import nearest


class TestNearestObject(unittest.TestCase):
    def setUp(self) -> None:
        self.config = aprsd_config.DEFAULT_CONFIG_DICT

    def _nearestObject(self):
        return nearest.NearestObjectPlugin(config=self.config)

    def test_nearest_object_latlon_US_Virginia(self):
        no = self._nearestObject()
        # Virginia
        lat_str = "37.58509827"
        lon_str = "-79.05139923"
        actual = no._get_latlon(lat_str, lon_str)
        expected = "3735.11N/07903.08W"
        self.assertEqual(expected, actual)

    def test_nearest_object_latlon_US_California(self):
        no = self._nearestObject()
        # California
        lat_str = "37.4538002"
        lon_str = "-122.18199921"
        actual = no._get_latlon(lat_str, lon_str)
        expected = "3727.23N/12210.92W"
        self.assertEqual(expected, actual)

    def test_nearest_object_latlon_US_Florida(self):
        no = self._nearestObject()
        # Florida
        lat_str = "30.42130089"
        lon_str = "-87.21690369"
        actual = no._get_latlon(lat_str, lon_str)
        expected = "3025.28N/08713.01W"
        self.assertEqual(expected, actual)

    def test_nearest_object_latlon_Peru(self):
        no = self._nearestObject()
        # Peru
        lat_str = "-12.0943"
        lon_str = "-77.0164"
        actual = no._get_latlon(lat_str, lon_str)
        expected = "1205.66S/07700.98W"
        self.assertEqual(expected, actual)

    def test_nearest_object_latlon_Germany(self):
        no = self._nearestObject()
        # Peru
        lat_str = "49.8096722"
        lon_str = "12.437758"
        actual = no._get_latlon(lat_str, lon_str)
        expected = "4948.58N/01226.27E"
        self.assertEqual(expected, actual)

    def test_nearest_object_latlon_India(self):
        no = self._nearestObject()
        # Peru
        lat_str = "11.63640022"
        lon_str = "76.20439911"
        actual = no._get_latlon(lat_str, lon_str)
        expected = "1138.18N/07612.26E"
        self.assertEqual(expected, actual)

    def test_nearest_object_latlon_austrailia(self):
        no = self._nearestObject()
        # Peru
        lat_str = "-37.88140106"
        lon_str = "145.21800232"
        actual = no._get_latlon(lat_str, lon_str)
        expected = "3752.88S/14513.08E"
        self.assertEqual(expected, actual)

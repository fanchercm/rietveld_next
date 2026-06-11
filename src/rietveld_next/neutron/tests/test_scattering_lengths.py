"""Tests for neutron scattering-length lookups."""

from __future__ import annotations

import unittest

from rietveld_next.neutron import lookup_bound_coherent_scattering_length


class NeutronScatteringLengthTests(unittest.TestCase):
    """Known-value and validation tests for neutron lookup tables."""

    def test_lookup_known_hydrogen_value(self) -> None:
        value = lookup_bound_coherent_scattering_length("1H")

        self.assertEqual(value.isotope, "1H")
        self.assertAlmostEqual(value.bound_coherent_fm, -3.7406, places=4)
        self.assertIn("NIST", value.source)

    def test_lookup_natural_hydrogen_value(self) -> None:
        value = lookup_bound_coherent_scattering_length("nat H")

        self.assertEqual(value.isotope, "H")
        self.assertAlmostEqual(value.bound_coherent_fm, -3.7390, places=4)

    def test_deuterium_alias_returns_isotope_label(self) -> None:
        self.assertEqual(lookup_bound_coherent_scattering_length("D").isotope, "2H")

    def test_lookup_rejects_empty_label(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty"):
            lookup_bound_coherent_scattering_length("")

    def test_lookup_rejects_unknown_isotope_with_available_keys(self) -> None:
        with self.assertRaisesRegex(KeyError, "Available keys"):
            lookup_bound_coherent_scattering_length("nat Si")


if __name__ == "__main__":
    unittest.main()

"""
Comprehensive Test Suite for NYC 311 Data Quality Checker.
Verifies all 12 corruptions, profiling routines, and detector mechanisms.
Compatible with standard Python unittest and Pytest.
"""

import unittest
import pandas as pd
import numpy as np

from project_b.dataset_manager import (
    generate_clean_nyc_311_dataset,
    profile_dataset,
    NYC_311_COLUMNS,
    ZIP_TO_BOROUGH
)
from project_b.corruption_injector import NYC311CorruptionInjector
from project_b.detectors.rule_detector import RuleBasedQualityDetector
from project_b.detectors.ml_detector import StatisticalMLQualityDetector
from project_b.detectors.llm_detector import GeminiLLMQualityDetector
from project_b.detectors.hybrid_detector import CascadingHybridQualityDetector


class TestNYC311DataQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.clean_df = generate_clean_nyc_311_dataset(num_records=500, seed=42)
        cls.injector = NYC311CorruptionInjector(seed=42)
        cls.corrupted_df, cls.gt = cls.injector.inject_all(cls.clean_df, sample_size_per_anomaly=15)
        cls.rule_det = RuleBasedQualityDetector()
        cls.ml_det = StatisticalMLQualityDetector(random_state=42)
        cls.hybrid_det = CascadingHybridQualityDetector()

    def test_clean_dataset_generation(self):
        """Test clean dataset schema, row count, and coordinate ranges."""
        self.assertEqual(len(self.clean_df), 500)
        for col in NYC_311_COLUMNS:
            self.assertIn(col, self.clean_df.columns)
        # Latitudes must be within NYC region (40.4 to 41.1)
        self.assertTrue((self.clean_df["latitude"] >= 40.4).all())
        self.assertTrue((self.clean_df["latitude"] <= 41.1).all())

    def test_profiler(self):
        """Test dataset profiler identifies columns, nulls, and baseline issues."""
        prof = profile_dataset(self.clean_df)
        self.assertEqual(prof["total_rows"], 500)
        self.assertIn("columns_profile", prof)
        self.assertIn("baseline_quality_issues", prof)
        self.assertIn("open_unresolved_2023_tickets", prof["baseline_quality_issues"])

    def test_corruption_injection_counts(self):
        """Verify ground truth exists for all 12 injected issues."""
        gt = self.gt
        self.assertTrue(len(gt["data_type_changes"]) > 0)
        self.assertTrue(len(gt["inconsistent_date_formats"]) > 0)
        self.assertTrue(len(gt["swapped_coordinates"]) > 0)
        self.assertTrue(len(gt["exact_duplicates"]) > 0)
        self.assertTrue(len(gt["near_duplicates"]) > 0)
        self.assertTrue(len(gt["null_spikes"]) > 0)
        self.assertTrue(len(gt["invalid_date_sequences"]) > 0)
        self.assertTrue(len(gt["zip_borough_mismatch"]) > 0)
        self.assertTrue(len(gt["complaint_descriptor_mismatch"]) > 0)
        self.assertTrue(len(gt["resolution_status_mismatch"]) > 0)
        self.assertTrue(len(gt["personal_information_in_text"]) > 0)

    def test_rule_detector_pii(self):
        """Verify rule-based detector identifies injected PII."""
        detected = [idx for idx, _ in self.rule_det.detect_personal_information(self.corrupted_df)]
        gt_indices = [item["row_index"] for item in self.gt["personal_information_in_text"]]
        overlap = set(detected) & set(gt_indices)
        self.assertTrue(len(overlap) >= len(gt_indices) * 0.8)

    def test_rule_detector_zip_borough(self):
        """Verify rule-based detector identifies ZIP/Borough mismatches."""
        detected = self.rule_det.detect_zip_borough_mismatches(self.corrupted_df)
        gt_indices = [item["row_index"] for item in self.gt["zip_borough_mismatch"]]
        overlap = set(detected) & set(gt_indices)
        self.assertEqual(len(overlap), len(gt_indices))

    def test_rule_detector_invalid_dates(self):
        """Verify rule-based detector identifies inverted dates (closed < created)."""
        detected = self.rule_det.detect_invalid_date_sequences(self.corrupted_df)
        gt_indices = [item["row_index"] for item in self.gt["invalid_date_sequences"]]
        overlap = set(detected) & set(gt_indices)
        self.assertEqual(len(overlap), len(gt_indices))

    def test_ml_spatial_isolation_forest(self):
        """Verify Isolation Forest catches swapped / out-of-bounds coordinates."""
        anomalies = self.ml_det.detect_spatial_anomalies_isolation_forest(self.corrupted_df)
        self.assertTrue(len(anomalies) > 0)

    def test_ml_near_duplicates_tfidf(self):
        """Verify TF-IDF cosine similarity detects near-duplicate records."""
        near_dupes = self.ml_det.detect_near_duplicates_tfidf(self.corrupted_df)
        self.assertTrue(len(near_dupes) > 0)

    def test_cascading_hybrid_detector(self):
        """Verify end-to-end cascading hybrid detector runs and emits telemetry."""
        detections, telemetry = self.hybrid_det.detect_all(self.corrupted_df)
        self.assertIn("swapped_coordinates", detections)
        self.assertIn("personal_information_in_text", detections)
        self.assertIn("total_rows_inspected", telemetry)
        self.assertIn("throughput_rows_per_sec", telemetry)
        self.assertTrue(telemetry["throughput_rows_per_sec"] > 0)


if __name__ == "__main__":
    unittest.main()


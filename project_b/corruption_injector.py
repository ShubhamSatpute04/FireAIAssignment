"""
Corruption Injector for NYC 311 Service Requests.
Injects 12 realistic data quality degradations and records exact ground-truth labels:
  1. Missing/renamed columns
  2. Data type changes
  3. Inconsistent date formats
  4. Swapped coordinates
  5. Exact duplicates
  6. Near-duplicates
  7. Null spikes
  8. Invalid date sequences
  9. ZIP/borough mismatch
  10. Complaint/descriptor mismatch
  11. Resolution/status mismatch
  12. Personal information in text (PII)
"""

import random
import copy
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from project_b.dataset_manager import BOROUGH_ZIP_MAP, COMPLAINT_CATALOG


class NYC311CorruptionInjector:
    """
    Injects 12 controlled data corruptions into NYC 311 service request datasets.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def inject_all(self, df: pd.DataFrame, sample_size_per_anomaly: int = 25) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Applies all 12 corruptions to a copy of df and tracks ground truth labels.
        """
        cdf = df.copy()
        n = len(cdf)
        k = min(sample_size_per_anomaly, n // 15)

        ground_truth: Dict[str, Any] = {
            "missing_renamed_columns": {},
            "data_type_changes": [],
            "inconsistent_date_formats": [],
            "swapped_coordinates": [],
            "exact_duplicates": [],
            "near_duplicates": [],
            "null_spikes": [],
            "invalid_date_sequences": [],
            "zip_borough_mismatch": [],
            "complaint_descriptor_mismatch": [],
            "resolution_status_mismatch": [],
            "personal_information_in_text": []
        }

        # 1. Missing / Renamed Columns (Record schema level)
        # We rename 'incident_zip' -> 'postal_code' and drop 'location_type' in an exported schema test
        ground_truth["missing_renamed_columns"] = {
            "renamed": {"incident_zip": "postal_code"},
            "dropped": ["location_type"]
        }

        # 2. Data Type Changes
        idx_dtype = random.sample(range(n), k)
        for idx in idx_dtype:
            original = cdf.at[idx, "latitude"]
            # Convert float latitude to string with degree symbol "40.7128° N"
            cdf.at[idx, "latitude"] = f"{original:.4f}° N"
            ground_truth["data_type_changes"].append({
                "row_index": idx,
                "column": "latitude",
                "original": original,
                "corrupted": cdf.at[idx, "latitude"]
            })

        # 3. Inconsistent Date Formats
        idx_dates = random.sample(range(n), k)
        for idx in idx_dates:
            original = cdf.at[idx, "created_date"]
            # Corrupt into ISO 8601 or European DD-MM-YYYY or epoch
            choice = random.choice(["iso", "euro", "epoch"])
            if choice == "iso":
                corrupted = "2023-07-15T14:30:00Z"
            elif choice == "euro":
                corrupted = "15/07/2023 14:30:00"
            else:
                corrupted = "1689431400"  # Raw epoch timestamp string
            cdf.at[idx, "created_date"] = corrupted
            ground_truth["inconsistent_date_formats"].append({
                "row_index": idx,
                "column": "created_date",
                "original": original,
                "corrupted": corrupted
            })

        # 4. Swapped Coordinates
        idx_swap = random.sample(range(n), k)
        for idx in idx_swap:
            lat = cdf.at[idx, "latitude"]
            lon = cdf.at[idx, "longitude"]
            # Ensure they are numeric before swapping
            try:
                lat_num = float(str(lat).replace("° N", ""))
                lon_num = float(str(lon).replace("° W", ""))
                cdf.at[idx, "latitude"] = lon_num
                cdf.at[idx, "longitude"] = lat_num
                ground_truth["swapped_coordinates"].append({
                    "row_index": idx,
                    "original_lat": lat_num,
                    "original_lon": lon_num,
                    "swapped_lat": lon_num,
                    "swapped_lon": lat_num
                })
            except Exception:
                pass

        # 5. Exact Duplicates
        idx_dupe = random.sample(range(n), k)
        dupe_rows = cdf.iloc[idx_dupe].copy()
        start_dupe_idx = len(cdf)
        cdf = pd.concat([cdf, dupe_rows], ignore_index=True)
        for i, orig_idx in enumerate(idx_dupe):
            ground_truth["exact_duplicates"].append({
                "duplicate_row_index": start_dupe_idx + i,
                "original_row_index": orig_idx,
                "unique_key": cdf.at[orig_idx, "unique_key"]
            })

        # 6. Near-Duplicates (Same ticket re-filed with typo in address or slight timestamp jitter)
        idx_near = random.sample(range(n), k)
        near_rows = []
        for i, idx in enumerate(idx_near):
            row = cdf.iloc[idx].copy()
            row["unique_key"] = int(row["unique_key"]) + 999000 + i
            orig_addr = str(row["incident_address"])
            row["incident_address"] = orig_addr.replace("AVE", "AVENUE").replace("ST", "STREET") + " APT 2B"
            row["resolution_description"] = str(row["resolution_description"]) + " (Citizen callback requested)"
            near_rows.append(row)
            ground_truth["near_duplicates"].append({
                "original_row_index": idx,
                "near_duplicate_unique_key": row["unique_key"],
                "original_address": orig_addr,
                "modified_address": row["incident_address"]
            })
        start_near_idx = len(cdf)
        cdf = pd.concat([cdf, pd.DataFrame(near_rows)], ignore_index=True)
        for i, item in enumerate(ground_truth["near_duplicates"]):
            item["near_duplicate_row_index"] = start_near_idx + i

        # 7. Null Spikes (Sudden abnormal blast of nulls in incident_zip)
        spike_start = random.randint(100, n - k - 50)
        idx_null_spike = list(range(spike_start, spike_start + k))
        for idx in idx_null_spike:
            orig = cdf.at[idx, "incident_zip"]
            cdf.at[idx, "incident_zip"] = np.nan
            ground_truth["null_spikes"].append({
                "row_index": idx,
                "column": "incident_zip",
                "original": orig
            })

        # 8. Invalid Date Sequences (Closed date precedes Created date)
        # Filter rows with non-null closed_date
        closed_indices = cdf[cdf["closed_date"].notna()].index.tolist()
        idx_invalid_seq = random.sample(closed_indices, min(k, len(closed_indices)))
        for idx in idx_invalid_seq:
            orig_created = cdf.at[idx, "created_date"]
            orig_closed = cdf.at[idx, "closed_date"]
            # Swap them or set closed date to 2022
            corrupted_closed = "01/01/2022 10:00:00 AM"
            cdf.at[idx, "closed_date"] = corrupted_closed
            ground_truth["invalid_date_sequences"].append({
                "row_index": idx,
                "created_date": orig_created,
                "corrupted_closed_date": corrupted_closed,
                "issue": "Closed Date earlier than Created Date"
            })

        # 9. ZIP / Borough Mismatch
        idx_zip_mismatch = random.sample(range(n), k)
        mismatch_targets = {
            "MANHATTAN": ("BROOKLYN", "11201"),
            "BROOKLYN": ("STATEN ISLAND", "10301"),
            "QUEENS": ("MANHATTAN", "10001"),
            "BRONX": ("QUEENS", "11354"),
            "STATEN ISLAND": ("BRONX", "10451")
        }
        for idx in idx_zip_mismatch:
            orig_borough = cdf.at[idx, "borough"]
            wrong_borough, wrong_zip = mismatch_targets.get(orig_borough, ("MANHATTAN", "10001"))
            # Assign Manhattan zip to Brooklyn borough
            cdf.at[idx, "incident_zip"] = wrong_zip
            ground_truth["zip_borough_mismatch"].append({
                "row_index": idx,
                "borough": orig_borough,
                "mismatched_zip": wrong_zip,
                "expected_borough_for_zip": wrong_borough
            })

        # 10. Complaint / Descriptor Mismatch
        idx_mismatch_desc = random.sample(range(n), k)
        for idx in idx_mismatch_desc:
            orig_comp = cdf.at[idx, "complaint_type"]
            orig_desc = cdf.at[idx, "descriptor"]
            # Assign an absurd descriptor
            corrupted_desc = "Pothole in middle of highway" if "Noise" in orig_comp else "Loud stereo / block party"
            cdf.at[idx, "descriptor"] = corrupted_desc
            ground_truth["complaint_descriptor_mismatch"].append({
                "row_index": idx,
                "complaint_type": orig_comp,
                "original_descriptor": orig_desc,
                "corrupted_descriptor": corrupted_desc
            })

        # 11. Resolution / Status Mismatch
        idx_status_mismatch = random.sample(range(n), k)
        for idx in idx_status_mismatch:
            orig_status = cdf.at[idx, "status"]
            orig_res = cdf.at[idx, "resolution_description"]
            if orig_status == "Closed":
                # Marked Closed but resolution says awaiting initial inspector
                corrupted_res = "The complaint has been forwarded to the local precinct and is currently pending initial field dispatch."
            else:
                # Marked Open but resolution says fully resolved and violation issued
                cdf.at[idx, "status"] = "Open"
                corrupted_res = "The Department of Buildings inspected the premises, corrected the violation, and the case has been closed."

            cdf.at[idx, "resolution_description"] = corrupted_res
            ground_truth["resolution_status_mismatch"].append({
                "row_index": idx,
                "status": cdf.at[idx, "status"],
                "corrupted_resolution": corrupted_res
            })

        # 12. Personal Information in Text (PII)
        idx_pii = random.sample(range(n), k)
        pii_samples = [
            ("Phone", "Caller contact number is (212) 555-0199 for gate access."),
            ("SSN", "Complainant verified identity using SSN: 123-45-6789."),
            ("Email", "Please direct all summons documents to citizen.smith99@nycmail.org."),
            ("CreditCard", "Refund processing fee paid via card 4111-2222-3333-4444."),
            ("Phone", "Direct mobile of tenant: 917-888-2341.")
        ]
        for idx in idx_pii:
            orig_res = str(cdf.at[idx, "resolution_description"])
            pii_type, pii_text = random.choice(pii_samples)
            cdf.at[idx, "resolution_description"] = f"{orig_res} Note: {pii_text}"
            ground_truth["personal_information_in_text"].append({
                "row_index": idx,
                "pii_type": pii_type,
                "pii_snippet": pii_text
            })

        return cdf, ground_truth

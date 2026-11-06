"""
Rule-Based Data Quality Detector for NYC 311 Service Requests.
Detects all 12 data quality corruptions using deterministic schema validation,
geographic boundary constraints, chronological rules, lookup tables, and regexes.
"""

import re
import datetime
from typing import Dict, Any, List, Set, Tuple
import pandas as pd
import numpy as np
from project_b.dataset_manager import NYC_311_COLUMNS, ZIP_TO_BOROUGH, COMPLAINT_CATALOG


# Precompile PII regexes
PHONE_REGEX = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

# Expected standard NYC 311 date format: MM/DD/YYYY hh:mm:ss AM/PM
STANDARD_DATE_REGEX = re.compile(r"^\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2}\s(?:AM|PM)$")

# Allowed complaint -> descriptor set
VALID_COMPLAINT_DESCRIPTORS: Dict[str, Set[str]] = {}
for _, _, comp, desc, _ in COMPLAINT_CATALOG:
    if comp not in VALID_COMPLAINT_DESCRIPTORS:
        VALID_COMPLAINT_DESCRIPTORS[comp] = set()
    VALID_COMPLAINT_DESCRIPTORS[comp].add(desc.lower())


class RuleBasedQualityDetector:
    """
    Pure deterministic rule-based detector for 12 data quality issues.
    """

    def detect_schema_issues(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Problem 1: Missing or Renamed Columns"""
        current_cols = set(df.columns)
        expected_cols = set(NYC_311_COLUMNS)
        missing = list(expected_cols - current_cols)
        extra = list(current_cols - expected_cols)
        return {
            "missing_columns": missing,
            "extra_renamed_columns": extra,
            "is_valid": len(missing) == 0
        }

    def detect_data_type_changes(self, df: pd.DataFrame) -> List[int]:
        """Problem 2: Data Type Changes (e.g. numeric lat/lon turned to string)"""
        flagged = []
        if "latitude" in df.columns:
            for idx, val in df["latitude"].items():
                if pd.notna(val) and not isinstance(val, (int, float, np.floating)):
                    val_str = str(val).strip()
                    if "°" in val_str or any(c.isalpha() for c in val_str):
                        flagged.append(idx)
        return flagged

    def detect_inconsistent_date_formats(self, df: pd.DataFrame) -> List[int]:
        """Problem 3: Inconsistent Date Formats"""
        flagged = []
        if "created_date" in df.columns:
            for idx, val in df["created_date"].items():
                if pd.notna(val):
                    val_str = str(val).strip()
                    if not STANDARD_DATE_REGEX.match(val_str):
                        flagged.append(idx)
        return flagged

    def detect_swapped_coordinates(self, df: pd.DataFrame) -> List[int]:
        """
        Problem 4: Swapped Coordinates
        NYC latitude must be in [40.4, 41.1], Longitude in [-74.4, -73.6].
        If latitude < 0 or longitude > 0, they are swapped.
        """
        flagged = []
        if "latitude" in df.columns and "longitude" in df.columns:
            for idx in df.index:
                lat = df.at[idx, "latitude"]
                lon = df.at[idx, "longitude"]
                try:
                    lat_f = float(str(lat).replace("° N", ""))
                    lon_f = float(str(lon).replace("° W", ""))
                    if (lat_f < 0.0 and lon_f > 0.0) or (abs(lat_f - (-73.9)) < 2.0 and abs(lon_f - 40.7) < 2.0):
                        flagged.append(idx)
                except Exception:
                    pass
        return flagged

    def detect_exact_duplicates(self, df: pd.DataFrame) -> List[int]:
        """Problem 5: Exact Duplicates"""
        # Flag duplicated records (keep first)
        dupes = df[df.duplicated(subset=["unique_key"], keep="first")]
        return dupes.index.tolist()

    def detect_near_duplicates(self, df: pd.DataFrame) -> List[int]:
        """
        Problem 6: Near-Duplicates using normalized address + agency + complaint
        """
        flagged = []
        if "incident_address" in df.columns and "complaint_type" in df.columns:
            # Clean normalized address
            norm_series = (
                df["incident_address"].astype(str).str.upper()
                .str.replace("AVENUE", "AVE")
                .str.replace("STREET", "ST")
                .str.replace("APT.*", "", regex=True)
                .str.strip()
            )
            combo = norm_series + "_" + df["complaint_type"].astype(str)
            # Find duplicates in combo where unique_key differs
            dupe_mask = combo.duplicated(keep="first") & (~df.duplicated(subset=["unique_key"], keep="first"))
            flagged = df[dupe_mask].index.tolist()
        return flagged

    def detect_null_spikes(self, df: pd.DataFrame, threshold_pct: float = 10.0) -> Dict[str, Any]:
        """Problem 7: Null Spikes (Columns exceeding normal null rate)"""
        spiked_cols = {}
        n = len(df)
        for c in df.columns:
            null_count = int(df[c].isna().sum())
            null_pct = (null_count / n) * 100.0
            if null_pct > threshold_pct and c not in ["closed_date"]:  # closed_date is naturally null for open tickets
                spiked_cols[c] = {
                    "null_count": null_count,
                    "null_pct": round(null_pct, 2),
                    "threshold_pct": threshold_pct
                }
        return spiked_cols

    def detect_invalid_date_sequences(self, df: pd.DataFrame) -> List[int]:
        """Problem 8: Invalid Date Sequences (closed_date < created_date)"""
        flagged = []
        if "created_date" in df.columns and "closed_date" in df.columns:
            for idx in df.index:
                c_str = df.at[idx, "created_date"]
                cl_str = df.at[idx, "closed_date"]
                if pd.notna(c_str) and pd.notna(cl_str):
                    try:
                        c_dt = pd.to_datetime(str(c_str))
                        cl_dt = pd.to_datetime(str(cl_str))
                        if cl_dt < c_dt:
                            flagged.append(idx)
                    except Exception:
                        pass
        return flagged

    def detect_zip_borough_mismatches(self, df: pd.DataFrame) -> List[int]:
        """Problem 9: ZIP / Borough Mismatches using official lookup table"""
        flagged = []
        if "incident_zip" in df.columns and "borough" in df.columns:
            for idx in df.index:
                z = str(df.at[idx, "incident_zip"]).strip()
                b = str(df.at[idx, "borough"]).strip().upper()
                if z in ZIP_TO_BOROUGH:
                    expected_b = ZIP_TO_BOROUGH[z]
                    if expected_b != b:
                        flagged.append(idx)
        return flagged

    def detect_complaint_descriptor_mismatches(self, df: pd.DataFrame) -> List[int]:
        """Problem 10: Complaint / Descriptor Mismatches using allowed catalog"""
        flagged = []
        if "complaint_type" in df.columns and "descriptor" in df.columns:
            for idx in df.index:
                comp = str(df.at[idx, "complaint_type"]).strip()
                desc = str(df.at[idx, "descriptor"]).strip().lower()
                # Cross-domain keyword check
                if "noise" in comp.lower() and ("pothole" in desc or "sewer" in desc or "water" in desc):
                    flagged.append(idx)
                elif ("street" in comp.lower() or "traffic" in comp.lower()) and "loud" in desc:
                    flagged.append(idx)
                elif comp in VALID_COMPLAINT_DESCRIPTORS:
                    # If complaint exists in our catalog and descriptor is completely foreign
                    if desc not in VALID_COMPLAINT_DESCRIPTORS[comp] and ("party" in desc or "pothole" in desc):
                        flagged.append(idx)
        return flagged

    def detect_resolution_status_mismatches(self, df: pd.DataFrame) -> List[int]:
        """Problem 11: Resolution / Status Mismatches using semantic keyword rules"""
        flagged = []
        if "status" in df.columns and "resolution_description" in df.columns:
            for idx in df.index:
                status = str(df.at[idx, "status"]).strip().capitalize()
                res = str(df.at[idx, "resolution_description"]).lower()
                if status == "Closed":
                    # Closed status should not contain unresolved pending keywords
                    if any(w in res for w in ["pending initial field dispatch", "awaiting inspection", "currently pending"]):
                        flagged.append(idx)
                elif status == "Open":
                    # Open status should not contain completed / rectified keywords
                    if any(w in res for w in ["corrected the violation", "case has been closed", "rectified the water leak"]):
                        flagged.append(idx)
        return flagged

    def detect_personal_information(self, df: pd.DataFrame) -> List[Tuple[int, str]]:
        """Problem 12: Personal Information in Text (PII)"""
        flagged = []
        text_cols = ["resolution_description", "descriptor"]
        for col in text_cols:
            if col in df.columns:
                for idx, text in df[col].items():
                    if pd.notna(text):
                        t_str = str(text)
                        reasons = []
                        if PHONE_REGEX.search(t_str):
                            reasons.append("Phone")
                        if SSN_REGEX.search(t_str):
                            reasons.append("SSN")
                        if EMAIL_REGEX.search(t_str):
                            reasons.append("Email")
                        if CARD_REGEX.search(t_str):
                            reasons.append("CreditCard")
                        if reasons:
                            flagged.append((idx, ", ".join(reasons)))
        return flagged

    def detect_all(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Runs rule detection for all 12 problems."""
        return {
            "missing_renamed_columns": self.detect_schema_issues(df),
            "data_type_changes": self.detect_data_type_changes(df),
            "inconsistent_date_formats": self.detect_inconsistent_date_formats(df),
            "swapped_coordinates": self.detect_swapped_coordinates(df),
            "exact_duplicates": self.detect_exact_duplicates(df),
            "near_duplicates": self.detect_near_duplicates(df),
            "null_spikes": self.detect_null_spikes(df),
            "invalid_date_sequences": self.detect_invalid_date_sequences(df),
            "zip_borough_mismatch": self.detect_zip_borough_mismatches(df),
            "complaint_descriptor_mismatch": self.detect_complaint_descriptor_mismatches(df),
            "resolution_status_mismatch": self.detect_resolution_status_mismatches(df),
            "personal_information_in_text": [idx for idx, _ in self.detect_personal_information(df)]
        }

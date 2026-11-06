"""
NYC 311 Service Requests (2023) Dataset Manager & Profiler.
Generates realistic representative NYC 311 2023 records matching the official NYC OpenData schema,
profiles data distributions, and identifies baseline quality issues with counts and concrete examples.
"""

import random
import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np


# Official NYC Open Data 311 Columns
NYC_311_COLUMNS = [
    "unique_key",
    "created_date",
    "closed_date",
    "agency",
    "agency_name",
    "complaint_type",
    "descriptor",
    "location_type",
    "incident_zip",
    "incident_address",
    "street_name",
    "city",
    "status",
    "due_date",
    "resolution_description",
    "resolution_action_updated_date",
    "borough",
    "latitude",
    "longitude"
]

# Valid NYC Borough to ZIP code reference mapping
BOROUGH_ZIP_MAP = {
    "MANHATTAN": ["10001", "10002", "10003", "10011", "10016", "10019", "10025", "10036"],
    "BROOKLYN": ["11201", "11205", "11211", "11215", "11217", "11226", "11231", "11238"],
    "QUEENS": ["11101", "11354", "11355", "11375", "11385", "11415", "11432", "11434"],
    "BRONX": ["10451", "10452", "10456", "10458", "10467", "10468", "10471", "10473"],
    "STATEN ISLAND": ["10301", "10302", "10304", "10306", "10310", "10312", "10314"]
}

# Reverse mapping
ZIP_TO_BOROUGH = {}
for b, zips in BOROUGH_ZIP_MAP.items():
    for z in zips:
        ZIP_TO_BOROUGH[z] = b

# Valid NYC Agency - Complaint - Descriptor triples
COMPLAINT_CATALOG = [
    ("NYPD", "New York City Police Department", "Noise - Residential", "Loud Music/Party", "Residential Building/House"),
    ("NYPD", "New York City Police Department", "Noise - Street/Sidewalk", "Loud Talking", "Street/Sidewalk"),
    ("NYPD", "New York City Police Department", "Illegal Parking", "Blocked Hydrant", "Street/Sidewalk"),
    ("NYPD", "New York City Police Department", "Illegal Parking", "Posted Parking Sign Violation", "Street/Sidewalk"),
    ("DOT", "Department of Transportation", "Street Condition", "Pothole", "Street"),
    ("DOT", "Department of Transportation", "Traffic Signal Condition", "Controller Broken", "Intersection"),
    ("DEP", "Department of Environmental Protection", "Water System", "Hydrant Running Full", "Street"),
    ("DEP", "Department of Environmental Protection", "Sewer", "Catch Basin Clogged/Flooding", "Street"),
    ("DSNY", "Department of Sanitation", "Dirty Conditions", "Trash Collection Missed", "Sidewalk"),
    ("DSNY", "Department of Sanitation", "Sanitation Condition", "Overflowing Litter Basket", "Sidewalk"),
    ("HPD", "Housing Preservation and Development", "HEAT/HOT WATER", "ENTIRE BUILDING", "RESIDENTIAL BUILDING"),
    ("DOB", "Department of Buildings", "General Construction", "Working Without a Permit", "Building")
]

RESOLUTION_TEMPLATES = {
    "Closed": [
        "The Department of Transportation inspected the condition and verified that the repair has been completed.",
        "The Police Department responded to the complaint and took action to restore peace and quiet.",
        "The Department of Housing Preservation and Development inspected the property and the violation has been closed.",
        "The Department of Environmental Protection investigated and rectified the water leak condition."
    ],
    "Open": [
        "The request has been accepted by the agency and is awaiting inspection.",
        "The case has been routed to the local borough precinct for priority field review.",
        "An inspector has been dispatched to investigate the reported location."
    ],
    "Pending": [
        "The Department is reviewing the engineering drawings and permit history.",
        "A second notice of violation has been mailed to the property owner; hearing pending."
    ]
}


def generate_clean_nyc_311_dataset(num_records: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Generates a clean synthetic NYC 311 2023 dataset reflecting real NYC geographic,
    temporal, and operational characteristics.
    """
    random.seed(seed)
    np.random.seed(seed)

    base_time = datetime.datetime(2023, 1, 1, 0, 0, 0)
    records = []

    borough_weights = {"MANHATTAN": 0.28, "BROOKLYN": 0.32, "QUEENS": 0.22, "BRONX": 0.14, "STATEN ISLAND": 0.04}
    boroughs = list(borough_weights.keys())
    weights = list(borough_weights.values())

    # Approximate lat/long bounding boxes per borough
    coords_box = {
        "MANHATTAN": (40.7128, 40.8500, -74.0150, -73.9300),
        "BROOKLYN": (40.5800, 40.7100, -74.0400, -73.8600),
        "QUEENS": (40.6000, 40.7800, -73.9500, -73.7200),
        "BRONX": (40.8000, 40.9100, -73.9300, -73.7800),
        "STATEN ISLAND": (40.5000, 40.6400, -74.2500, -74.0600)
    }

    street_names = ["BROADWAY", "5TH AVE", "ATLANTIC AVE", "BEDFORD AVE", "GRAND CONCOURSE", "QUEENS BLVD", "HYLAN BLVD", "AMSTERDAM AVE"]

    for i in range(num_records):
        unique_key = 57000000 + i
        created_delta = datetime.timedelta(
            days=random.randint(0, 364),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        created_dt = base_time + created_delta

        status = random.choices(["Closed", "Open", "Pending"], weights=[0.85, 0.10, 0.05])[0]

        if status == "Closed":
            close_delta = datetime.timedelta(hours=random.randint(2, 72), minutes=random.randint(0, 59))
            closed_dt = created_dt + close_delta
            closed_str = closed_dt.strftime("%m/%d/%Y %I:%M:%S %p")
            res_str = random.choice(RESOLUTION_TEMPLATES["Closed"])
            res_upd_str = closed_str
        elif status == "Open":
            closed_str = None
            res_str = random.choice(RESOLUTION_TEMPLATES["Open"])
            res_upd_str = created_dt.strftime("%m/%d/%Y %I:%M:%S %p")
        else:
            closed_str = None
            res_str = random.choice(RESOLUTION_TEMPLATES["Pending"])
            res_upd_str = (created_dt + datetime.timedelta(hours=12)).strftime("%m/%d/%Y %I:%M:%S %p")

        created_str = created_dt.strftime("%m/%d/%Y %I:%M:%S %p")
        due_str = (created_dt + datetime.timedelta(days=7)).strftime("%m/%d/%Y %I:%M:%S %p")

        agency, agency_name, complaint, desc, loc_type = random.choice(COMPLAINT_CATALOG)
        borough = random.choices(boroughs, weights=weights)[0]
        zip_code = random.choice(BOROUGH_ZIP_MAP[borough])
        street = random.choice(street_names)
        address = f"{random.randint(100, 999)} {street}"
        city = borough if borough != "MANHATTAN" else "NEW YORK"

        lat_min, lat_max, lon_min, lon_max = coords_box[borough]
        lat = round(random.uniform(lat_min, lat_max), 6)
        lon = round(random.uniform(lon_min, lon_max), 6)

        records.append({
            "unique_key": unique_key,
            "created_date": created_str,
            "closed_date": closed_str,
            "agency": agency,
            "agency_name": agency_name,
            "complaint_type": complaint,
            "descriptor": desc,
            "location_type": loc_type,
            "incident_zip": zip_code,
            "incident_address": address,
            "street_name": street,
            "city": city,
            "status": status,
            "due_date": due_str,
            "resolution_description": res_str,
            "resolution_action_updated_date": res_upd_str,
            "borough": borough,
            "latitude": lat,
            "longitude": lon
        })

    return pd.DataFrame(records)


def profile_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Profiles the NYC 311 dataset and identifies existing baseline quality issues,
    returning counts, percentages, and real concrete examples.
    """
    total_rows = len(df)
    cols_profile = {}

    for c in df.columns:
        null_count = int(df[c].isna().sum())
        null_pct = round((null_count / total_rows) * 100.0, 2)
        cols_profile[c] = {
            "dtype": str(df[c].dtype),
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_values": int(df[c].nunique())
        }

    # Baseline Anomaly 1: Unclosed tickets from 2023
    open_tickets = df[df["status"] == "Open"]
    open_count = len(open_tickets)
    open_sample = open_tickets[["unique_key", "complaint_type", "created_date", "borough"]].head(2).to_dict(orient="records")

    # Baseline Anomaly 2: Closed tickets without closed_date
    anom_closed_missing = df[(df["status"] == "Closed") & (df["closed_date"].isna())]
    closed_missing_count = len(anom_closed_missing)
    closed_missing_sample = anom_closed_missing[["unique_key", "status", "resolution_description"]].head(2).to_dict(orient="records")

    # Baseline Anomaly 3: Duplicate unique keys
    dupe_keys = df[df.duplicated(subset=["unique_key"], keep=False)]
    dupe_count = len(dupe_keys)

    # Baseline Anomaly 4: Out-of-bounds coordinates
    coord_anom = df[(df["latitude"] < 40.4) | (df["latitude"] > 41.0) | (df["longitude"] < -74.4) | (df["longitude"] > -73.6)]
    coord_count = len(coord_anom)
    coord_sample = coord_anom[["unique_key", "latitude", "longitude", "borough"]].head(2).to_dict(orient="records")

    return {
        "total_rows": total_rows,
        "total_columns": len(df.columns),
        "columns_profile": cols_profile,
        "baseline_quality_issues": {
            "open_unresolved_2023_tickets": {
                "count": open_count,
                "pct": round((open_count / total_rows) * 100.0, 2),
                "description": "Tickets from 2023 still flagged as Open/Pending resolution",
                "sample_examples": open_sample
            },
            "closed_status_missing_closed_date": {
                "count": closed_missing_count,
                "pct": round((closed_missing_count / total_rows) * 100.0, 2),
                "description": "Tickets marked 'Closed' but missing timestamps in closed_date",
                "sample_examples": closed_missing_sample
            },
            "duplicate_unique_keys": {
                "count": dupe_count,
                "pct": round((dupe_count / total_rows) * 100.0, 2),
                "description": "Non-unique service request identifiers",
                "sample_examples": dupe_keys.head(2).to_dict(orient="records")
            },
            "out_of_bounds_geographic_coordinates": {
                "count": coord_count,
                "pct": round((coord_count / total_rows) * 100.0, 2),
                "description": "Coordinates falling outside the 5 NYC boroughs boundary box",
                "sample_examples": coord_sample
            }
        }
    }


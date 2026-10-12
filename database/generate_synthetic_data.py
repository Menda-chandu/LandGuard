"""
Script to generate 100 fully synthetic land records for LandGuard.
Generates:
1. sample_data/synthetic_land_records_100.csv
2. sample_data/synthetic_ownership_history_100.csv
3. sample_data/parcels_synthetic_100.geojson
4. database/seed_synthetic_100.sql
"""

import os
import csv
import json
from datetime import date

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAMPLE_DATA_DIR = os.path.join(PROJECT_ROOT, "sample_data")
DATABASE_DIR = os.path.join(PROJECT_ROOT, "database")

# Fictional Telugu/Indian Names
FIRST_NAMES = [
    "Kalyan Varma", "Sunitha Devi", "Venkatesh Prasad", "Anil Kumar", "Madhavi Latha",
    "Ravi Shankar", "Srinivas Rao", "Sita Mahalakshmi", "Prabhakar Raju", "Radhika Rani",
    "Rajesh Babu", "Padmavathi", "Venu Gopal", "Lakshmi Prasanna", "Nagaraju",
    "Swapna Kumari", "Mahesh Chandra", "Bhavani Shankar", "Geetha Madhuri", "Satish Varma",
    "Mohan Krishna", "Sireesha Devi", "Ramesh Babu", "Usha Rani", "Kishore Kumar",
    "Aparna Rao", "Sudhir Varma", "Kavitha Reddy", "Praveen Kumar", "Saritha Devi",
    "Vijay Bhaskar", "Deepika Rani", "Harish Chandra", "Sravani Devi", "Chandra Sekhar",
    "Anuradha Rao", "Suresh Kumar", "Lavanya Devi", "Phani Kumar", "Madhuri Latha",
    "Gautam Varma", "Sandhya Rani", "Kiran Kumar", "Divya Bharati", "Vamsi Krishna",
    "Sailaja Devi", "Tarun Kumar", "Swathi Rani", "Naresh Babu", "Manjula Devi",
    "Sanjay Varma", "Prasanna Kumar", "Hema Malini", "Bhupathi Raju", "Sirisha Rani",
    "Jagadish Chandra", "Roopa Devi", "Naveen Kumar", "Shobha Rani", "Purna Chandra",
    "Krishna Mohan", "Vandana Devi", "Sekhar Babu", "Tejaswi Rani", "Vinod Kumar",
    "Priyanka Devi", "Arun Kumar", "Mamatha Rani", "Ranganath Varma", "Haritha Devi"
]

SURNAMES = [
    "Dantuluri", "Mallampati", "Alapati", "Penmetsa", "Kanumuri",
    "Namburi", "Gokaraju", "Alluri", "Sagi", "Vegesna",
    "Mudunuri", "Byrraju", "Indukuri", "Dandu", "Rudraraju",
    "Datla", "Kalidindi", "Chintalapati", "Kothapalli", "Bhupathiraju",
    "Jampana", "Uppalapati", "Vatsavai", "Gadiraju", "Singireddy",
    "Marri", "Challa", "Boppana", "Kommineni", "Yalamanchili",
    "Devineni", "Velagapudi", "Kosaraju", "Pinnamaneni", "Nannapaneni",
    "Surapaneni", "Kaza", "Nallapati", "Mandava", "Chennupati",
    "Atluri", "Rayapati", "Koneru", "Yaragudipati", "Parvataneni",
    "Chukkapalli", "Potluri", "Guntupalli", "Nanduri", "Kakarla",
    "Katragadda", "Anne", "Dasari", "Maganti", "Vallabhaneni",
    "Jasti", "Motaparti", "Lingamaneni", "Koganti", "Movva",
    "Adusumilli", "Mullapudi", "Pendyala", "Chitturi", "Thota"
]

LOCATIONS = [
    {"village": "Narsingi", "mandal": "Gandipet", "district": "Ranga Reddy", "base_coord": (78.35, 17.38)},
    {"village": "Kokapet", "mandal": "Gandipet", "district": "Ranga Reddy", "base_coord": (78.33, 17.39)},
    {"village": "Tellapur", "mandal": "Ramachandrapuram", "district": "Sangareddy", "base_coord": (78.28, 17.45)},
    {"village": "Mokila", "mandal": "Shankarpally", "district": "Ranga Reddy", "base_coord": (78.20, 17.40)},
    {"village": "Shankarpally", "mandal": "Shankarpally", "district": "Ranga Reddy", "base_coord": (78.18, 17.43)},
    {"village": "Manikonda", "mandal": "Gandipet", "district": "Ranga Reddy", "base_coord": (78.38, 17.40)},
    {"village": "Puppalguda", "mandal": "Gandipet", "district": "Ranga Reddy", "base_coord": (78.37, 17.41)},
    {"village": "Kollur", "mandal": "Ramachandrapuram", "district": "Sangareddy", "base_coord": (78.25, 17.48)},
    {"village": "Vattinagulapally", "mandal": "Gandipet", "district": "Ranga Reddy", "base_coord": (78.30, 17.41)},
    {"village": "Khanapur", "mandal": "Gandipet", "district": "Ranga Reddy", "base_coord": (78.31, 17.36)},
    {"village": "Janwada", "mandal": "Shankarpally", "district": "Ranga Reddy", "base_coord": (78.24, 17.37)},
    {"village": "Aziznagar", "mandal": "Moinabad", "district": "Ranga Reddy", "base_coord": (78.32, 17.33)},
    {"village": "Appa Junction", "mandal": "Rajendranagar", "district": "Ranga Reddy", "base_coord": (78.36, 17.35)},
    {"village": "Peeramcheruvu", "mandal": "Rajendranagar", "district": "Ranga Reddy", "base_coord": (78.38, 17.36)}
]

DOC_TYPES = ["Sale Deed", "Gift Deed", "Partition Deed", "Settlement Deed", "Inheritance Mutation"]

def generate_dataset():
    land_records = []
    ownership_history = []
    geojson_features = []

    hist_counter = 1

    # =========================================================================
    # Group A: 70 Normal Records (SYN-REC-001 to SYN-REC-070)
    # Clean Title, Perfect Alignment, Legitimate History Chains
    # =========================================================================
    for i in range(1, 71):
        rec_id = f"SYN-REC-{i:03d}"
        first_name = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
        surname = SURNAMES[(i - 1) % len(SURNAMES)]
        owner_name = f"{first_name} {surname}"
        
        survey_num = f"SYN-1{i:02d}/A"
        area = round(0.50 + ((i * 17) % 115) * 0.10, 2)
        if area > 12.0:
            area = round(area - 5.0, 2)

        loc = LOCATIONS[(i - 1) % len(LOCATIONS)]
        reg_num = f"SYN-REG-20{15 + (i % 9):02d}-{1000 + i}"
        reg_year = 2016 + (i % 8)
        reg_month = (i % 12) + 1
        reg_day = (i % 25) + 1
        reg_date = date(reg_year, reg_month, reg_day).isoformat()
        doc_type = DOC_TYPES[i % len(DOC_TYPES)]

        land_records.append({
            "record_id": rec_id,
            "owner_name": owner_name,
            "survey_number": survey_num,
            "land_area_acres": f"{area:.2f}",
            "village": loc["village"],
            "mandal": loc["mandal"],
            "district": loc["district"],
            "state": "Telangana",
            "registration_number": reg_num,
            "registration_date": reg_date,
            "document_type": doc_type
        })

        # Legitimate History Chain
        # 1. Historical Original Grant / Ancestral Title (e.g. 1995-2010)
        ancestor_name = f"{surname} Ramaswamy" if i % 2 == 0 else f"{surname} Narayana Rao"
        grant_year = 1995 + (i % 14)
        grant_date = date(grant_year, (i % 11) + 1, (i % 27) + 1).isoformat()
        
        ownership_history.append({
            "history_id": f"SYN-HIST-{hist_counter:03d}",
            "survey_number": survey_num,
            "owner_name": ancestor_name,
            "transfer_date": grant_date,
            "transfer_type": "Original Grant" if i % 2 == 0 else "Ancestral Partition"
        })
        hist_counter += 1

        # Intermediate transfer if older grant
        if i % 3 == 0:
            inter_name = f"{surname} Subba Rao"
            inter_year = grant_year + 8
            inter_date = date(inter_year, 5, 12).isoformat()
            ownership_history.append({
                "history_id": f"SYN-HIST-{hist_counter:03d}",
                "survey_number": survey_num,
                "owner_name": inter_name,
                "transfer_date": inter_date,
                "transfer_type": "Inheritance Mutation"
            })
            hist_counter += 1

        # 2. Conveyance to Current Title Holder
        ownership_history.append({
            "history_id": f"SYN-HIST-{hist_counter:03d}",
            "survey_number": survey_num,
            "owner_name": owner_name,
            "transfer_date": reg_date,
            "transfer_type": doc_type
        })
        hist_counter += 1

        # GIS Polygon Feature for Clean Spatial Match
        bx, by = loc["base_coord"]
        ox = ((i % 10) * 0.003)
        oy = (((i // 10) % 10) * 0.003)
        poly = [
            [round(bx + ox, 6), round(by + oy, 6)],
            [round(bx + ox + 0.002, 6), round(by + oy + 0.0005, 6)],
            [round(bx + ox + 0.0025, 6), round(by + oy - 0.002, 6)],
            [round(bx + ox + 0.0005, 6), round(by + oy - 0.0025, 6)],
            [round(bx + ox, 6), round(by + oy, 6)]
        ]

        geojson_features.append({
            "type": "Feature",
            "id": f"SYN-PARCEL-{i:03d}",
            "properties": {
                "survey_number": survey_num,
                "owner_name": owner_name,
                "land_area_acres": float(area),
                "village": loc["village"],
                "mandal": loc["mandal"],
                "district": loc["district"],
                "state": "Telangana",
                "risk_level": "LOW",
                "conflict_status": "Clean Synthetic Title"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly]
            }
        })

    # =========================================================================
    # Group B: 10 Duplicate Registration Cases (SYN-REC-071 to SYN-REC-080)
    # 5 pairs of overlapping/double-registered parcels
    # =========================================================================
    dup_pairs = [
        # Pair 1: Survey SYN-501/A
        {
            "rec1": ("SYN-REC-071", "SYN-501/A", "Ravi Kiran Nanduri", 4.00, "Mokila", "Shankarpally", "SYN-REG-2021-1071", "2021-03-10", "Sale Deed"),
            "rec2": ("SYN-REC-072", "SYN-501/A", "Sudhakar Rao Guntupalli", 4.00, "Mokila", "Shankarpally", "SYN-REG-2023-1072", "2023-08-22", "Duplicate Sale Deed")
        },
        # Pair 2: Survey SYN-502/B
        {
            "rec1": ("SYN-REC-073", "SYN-502/B", "Hema Malini Kakarla", 2.50, "Kokapet", "Gandipet", "SYN-REG-2022-1073", "2022-01-15", "Sale Deed"),
            "rec2": ("SYN-REC-074", "SYN-502/B", "Bhupathi Raju Varma", 2.50, "Kokapet", "Gandipet", "SYN-REG-2022-1074", "2022-02-10", "Conflicting Sale Deed")
        },
        # Pair 3: Survey SYN-503/C (Duplicate Reg Number)
        {
            "rec1": ("SYN-REC-075", "SYN-503/C", "Jagadish Chandra Anne", 3.20, "Tellapur", "Ramachandrapuram", "SYN-REG-DUP-001", "2020-06-18", "Sale Deed"),
            "rec2": ("SYN-REC-076", "SYN-503/C", "Roopa Devi Dasari", 3.20, "Tellapur", "Ramachandrapuram", "SYN-REG-DUP-001", "2020-07-25", "Duplicate Registration")
        },
        # Pair 4: Survey SYN-504/D
        {
            "rec1": ("SYN-REC-077", "SYN-504/D", "Naveen Kumar Maganti", 5.00, "Janwada", "Shankarpally", "SYN-REG-2019-1077", "2019-11-04", "Partition Deed"),
            "rec2": ("SYN-REC-078", "SYN-504/D", "Shobha Rani Vallabhaneni", 5.00, "Janwada", "Shankarpally", "SYN-REG-2023-1078", "2023-04-12", "Overlapping Sale Deed")
        },
        # Pair 5: Survey SYN-505/E
        {
            "rec1": ("SYN-REC-079", "SYN-505/E", "Purna Chandra Jasti", 1.75, "Narsingi", "Gandipet", "SYN-REG-2021-1079", "2021-09-30", "Sale Deed"),
            "rec2": ("SYN-REC-080", "SYN-505/E", "Krishna Mohan Motaparti", 1.75, "Narsingi", "Gandipet", "SYN-REG-2023-1080", "2023-10-14", "Unauthorized Resale")
        }
    ]

    for p_idx, pair in enumerate(dup_pairs):
        for side, (rid, snum, oname, area, vill, mand, rnum, rdate, dtype) in enumerate([pair["rec1"], pair["rec2"]]):
            distr = "Ranga Reddy" if vill != "Tellapur" else "Sangareddy"
            land_records.append({
                "record_id": rid,
                "owner_name": oname,
                "survey_number": snum,
                "land_area_acres": f"{area:.2f}",
                "village": vill,
                "mandal": mand,
                "district": distr,
                "state": "Telangana",
                "registration_number": rnum,
                "registration_date": rdate,
                "document_type": dtype
            })

            # History entry
            ownership_history.append({
                "history_id": f"SYN-HIST-{hist_counter:03d}",
                "survey_number": snum,
                "owner_name": oname,
                "transfer_date": rdate,
                "transfer_type": dtype
            })
            hist_counter += 1

        # Add single GeoJSON polygon for the disputed survey
        geojson_features.append({
            "type": "Feature",
            "id": f"SYN-PARCEL-DUP-{p_idx+1}",
            "properties": {
                "survey_number": pair["rec1"][1],
                "owner_name": pair["rec1"][2],
                "land_area_acres": pair["rec1"][3],
                "village": pair["rec1"][4],
                "mandal": pair["rec1"][5],
                "district": "Ranga Reddy",
                "state": "Telangana",
                "risk_level": "CRITICAL",
                "conflict_status": "Double Selling Duplicate Registration"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [78.20 + p_idx * 0.02, 17.38],
                    [78.20 + p_idx * 0.02 + 0.003, 17.381],
                    [78.20 + p_idx * 0.02 + 0.003, 17.378],
                    [78.20 + p_idx * 0.02, 17.378],
                    [78.20 + p_idx * 0.02, 17.38]
                ]]
            }
        })

    # =========================================================================
    # Group C: 20 Targeted Anomaly Records (SYN-REC-081 to SYN-REC-100)
    # =========================================================================
    
    # C.1 Owner Mismatches (SYN-REC-081 to SYN-REC-085)
    owner_mismatch_defs = [
        ("SYN-REC-081", "SYN-701/A", "Bhaskar Raju Kanumuri", 3.20, "Mokila", "Shankarpally", "SYN-REG-2020-1081", "2020-05-14", "Sale Deed"),
        ("SYN-REC-082", "SYN-702/B", "Nagendra Rao Potluri", 2.10, "Kokapet", "Gandipet", "SYN-REG-2021-1082", "2021-08-11", "Sale Deed"),
        ("SYN-REC-083", "SYN-703/C", "Sita Devi Byrraju", 4.50, "Tellapur", "Ramachandrapuram", "SYN-REG-2019-1083", "2019-12-04", "Gift Deed"),
        ("SYN-REC-084", "SYN-704/D", "Chandrasekhar Sagi", 1.65, "Narsingi", "Gandipet", "SYN-REG-2022-1084", "2022-03-29", "Sale Deed"),
        ("SYN-REC-085", "SYN-705/E", "Padma Rani Vegesna", 5.25, "Janwada", "Shankarpally", "SYN-REG-2023-1085", "2023-06-17", "Partition Deed")
    ]
    for rid, snum, oname, area, vill, mand, rnum, rdate, dtype in owner_mismatch_defs:
        distr = "Ranga Reddy" if vill != "Tellapur" else "Sangareddy"
        land_records.append({
            "record_id": rid,
            "owner_name": oname,
            "survey_number": snum,
            "land_area_acres": f"{area:.2f}",
            "village": vill,
            "mandal": mand,
            "district": distr,
            "state": "Telangana",
            "registration_number": rnum,
            "registration_date": rdate,
            "document_type": dtype
        })
        ownership_history.append({
            "history_id": f"SYN-HIST-{hist_counter:03d}",
            "survey_number": snum,
            "owner_name": oname,
            "transfer_date": rdate,
            "transfer_type": dtype
        })
        hist_counter += 1
        geojson_features.append({
            "type": "Feature",
            "id": f"SYN-PARCEL-{rid}",
            "properties": {
                "survey_number": snum,
                "owner_name": oname,
                "land_area_acres": area,
                "village": vill,
                "mandal": mand,
                "district": distr,
                "state": "Telangana",
                "risk_level": "HIGH",
                "conflict_status": "Owner Identity Mismatch"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[78.22, 17.39], [78.223, 17.391], [78.224, 17.388], [78.22, 17.388], [78.22, 17.39]]]
            }
        })

    # C.2 Land Area Mismatches / Inflations (SYN-REC-086 to SYN-REC-089)
    area_mismatch_defs = [
        ("SYN-REC-086", "SYN-801/A", "Dharma Rao Chitturi", 2.50, "Shankarpally", "Shankarpally", "SYN-REG-2021-1086", "2021-09-18", "Sale Deed"),
        ("SYN-REC-087", "SYN-802/B", "Anasuya Devi Kaza", 1.20, "Kokapet", "Gandipet", "SYN-REG-2022-1087", "2022-11-05", "Sale Deed"),
        ("SYN-REC-088", "SYN-803/C", "Somashekar Rao Movva", 4.50, "Mokila", "Shankarpally", "SYN-REG-2020-1088", "2020-04-14", "Gift Deed"),
        ("SYN-REC-089", "SYN-804/D", "Radha Kumari Nallapati", 3.00, "Narsingi", "Gandipet", "SYN-REG-2023-1089", "2023-05-20", "Sale Deed")
    ]
    for rid, snum, oname, area, vill, mand, rnum, rdate, dtype in area_mismatch_defs:
        land_records.append({
            "record_id": rid,
            "owner_name": oname,
            "survey_number": snum,
            "land_area_acres": f"{area:.2f}",
            "village": vill,
            "mandal": mand,
            "district": "Ranga Reddy",
            "state": "Telangana",
            "registration_number": rnum,
            "registration_date": rdate,
            "document_type": dtype
        })
        ownership_history.append({
            "history_id": f"SYN-HIST-{hist_counter:03d}",
            "survey_number": snum,
            "owner_name": oname,
            "transfer_date": rdate,
            "transfer_type": dtype
        })
        hist_counter += 1
        geojson_features.append({
            "type": "Feature",
            "id": f"SYN-PARCEL-{rid}",
            "properties": {
                "survey_number": snum,
                "owner_name": oname,
                "land_area_acres": area,
                "village": vill,
                "mandal": mand,
                "district": "Ranga Reddy",
                "state": "Telangana",
                "risk_level": "MEDIUM",
                "conflict_status": "Land Area Discrepancy"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[78.26, 17.41], [78.263, 17.412], [78.264, 17.409], [78.26, 17.409], [78.26, 17.41]]]
            }
        })

    # C.3 Survey Number Mismatch / Sub-division Discrepancies (SYN-REC-090 to SYN-REC-092)
    survey_mismatch_defs = [
        ("SYN-REC-090", "SYN-805/A", "Girish Varma Sagi", 3.40, "Tellapur", "Ramachandrapuram", "SYN-REG-2021-1090", "2021-02-12", "Sale Deed"),
        ("SYN-REC-091", "SYN-806/B", "Vijayalakshmi Rao", 2.80, "Puppalguda", "Gandipet", "SYN-REG-2022-1091", "2022-06-25", "Sale Deed"),
        ("SYN-REC-092", "SYN-807/C", "Madhusudhan Raju", 4.10, "Manikonda", "Gandipet", "SYN-REG-2020-1092", "2020-10-19", "Partition Deed")
    ]
    for rid, snum, oname, area, vill, mand, rnum, rdate, dtype in survey_mismatch_defs:
        distr = "Ranga Reddy" if vill != "Tellapur" else "Sangareddy"
        land_records.append({
            "record_id": rid,
            "owner_name": oname,
            "survey_number": snum,
            "land_area_acres": f"{area:.2f}",
            "village": vill,
            "mandal": mand,
            "district": distr,
            "state": "Telangana",
            "registration_number": rnum,
            "registration_date": rdate,
            "document_type": dtype
        })
        ownership_history.append({
            "history_id": f"SYN-HIST-{hist_counter:03d}",
            "survey_number": snum,
            "owner_name": oname,
            "transfer_date": rdate,
            "transfer_type": dtype
        })
        hist_counter += 1
        geojson_features.append({
            "type": "Feature",
            "id": f"SYN-PARCEL-{rid}",
            "properties": {
                "survey_number": snum,
                "owner_name": oname,
                "land_area_acres": area,
                "village": vill,
                "mandal": mand,
                "district": distr,
                "state": "Telangana",
                "risk_level": "HIGH",
                "conflict_status": "Cadastral Survey Discrepancy"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[78.29, 17.43], [78.293, 17.432], [78.294, 17.429], [78.29, 17.429], [78.29, 17.43]]]
            }
        })

    # C.4 Rapid Ownership Transfers / Flipping (SYN-REC-093 to SYN-REC-095)
    rapid_transfer_defs = [
        ("SYN-REC-093", "SYN-601/A", "Nitin Varma Sagi", 2.75, "Highland Fictional", "Chevella", "SYN-REG-2024-1093", "2024-02-02", "Rapid Resale"),
        ("SYN-REC-094", "SYN-602/B", "Kishore Varma Datla", 3.50, "Forest View Fictional", "Moinabad", "SYN-REG-2023-1094", "2023-12-08", "Rapid Resale"),
        ("SYN-REC-095", "SYN-603/C", "Vijay Bhaskar Alluri", 1.90, "Green Acres Fictional", "Shankarpally", "SYN-REG-2024-1095", "2024-02-28", "Rapid Resale")
    ]
    rapid_history_chains = [
        # Chain for 601/A: 3 transfers in 28 days
        [
            ("Prasad Varma Sagi", "2024-01-05", "Original Sale"),
            ("Naresh Varma Sagi", "2024-01-18", "Rapid Resale"),
            ("Nitin Varma Sagi", "2024-02-02", "Rapid Resale")
        ],
        # Chain for 602/B: 3 transfers in 28 days
        [
            ("Ramu Datla", "2023-11-10", "Original Sale"),
            ("Soma Raju Datla", "2023-11-25", "Rapid Resale"),
            ("Kishore Varma Datla", "2023-12-08", "Rapid Resale")
        ],
        # Chain for 603/C: 3 transfers in 27 days
        [
            ("Anil Alluri", "2024-02-01", "Original Sale"),
            ("Chiranjeevi Alluri", "2024-02-14", "Rapid Resale"),
            ("Vijay Bhaskar Alluri", "2024-02-28", "Rapid Resale")
        ]
    ]
    for idx, (rid, snum, oname, area, vill, mand, rnum, rdate, dtype) in enumerate(rapid_transfer_defs):
        land_records.append({
            "record_id": rid,
            "owner_name": oname,
            "survey_number": snum,
            "land_area_acres": f"{area:.2f}",
            "village": vill,
            "mandal": mand,
            "district": "Ranga Reddy",
            "state": "Telangana",
            "registration_number": rnum,
            "registration_date": rdate,
            "document_type": dtype
        })
        for h_owner, h_date, h_type in rapid_history_chains[idx]:
            ownership_history.append({
                "history_id": f"SYN-HIST-{hist_counter:03d}",
                "survey_number": snum,
                "owner_name": h_owner,
                "transfer_date": h_date,
                "transfer_type": h_type
            })
            hist_counter += 1
        geojson_features.append({
            "type": "Feature",
            "id": f"SYN-PARCEL-{rid}",
            "properties": {
                "survey_number": snum,
                "owner_name": oname,
                "land_area_acres": area,
                "village": vill,
                "mandal": mand,
                "district": "Ranga Reddy",
                "state": "Telangana",
                "risk_level": "HIGH",
                "conflict_status": "Suspicious Rapid Flipping"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[78.15 + idx * 0.03, 17.30], [78.152 + idx * 0.03, 17.302], [78.153 + idx * 0.03, 17.298], [78.15 + idx * 0.03, 17.298], [78.15 + idx * 0.03, 17.30]]]
            }
        })

    # C.5 Incomplete / Corrupt Records (SYN-REC-096 to SYN-REC-098)
    incomplete_defs = [
        ("SYN-REC-096", "SYN-901/A", "", 1.75, "Narsingi", "Gandipet", "SYN-REG-2022-1096", "", "Sale Deed"),
        ("SYN-REC-097", "SYN-902/B", "Sarath Chandra Datla", 2.40, "Kokapet", "Gandipet", "SYN-REG-2021-1097", "", "Patta Passbook"),
        ("SYN-REC-098", "SYN-903/C", "Subba Rao Penmetsa", 0.00, "Mokila", "Shankarpally", "SYN-REG-2023-1098", "2023-01-11", "Sale Deed")
    ]
    for rid, snum, oname, area, vill, mand, rnum, rdate, dtype in incomplete_defs:
        land_records.append({
            "record_id": rid,
            "owner_name": oname,
            "survey_number": snum,
            "land_area_acres": f"{area:.2f}",
            "village": vill,
            "mandal": mand,
            "district": "Ranga Reddy",
            "state": "Telangana",
            "registration_number": rnum,
            "registration_date": rdate,
            "document_type": dtype
        })
        if oname:
            ownership_history.append({
                "history_id": f"SYN-HIST-{hist_counter:03d}",
                "survey_number": snum,
                "owner_name": oname,
                "transfer_date": rdate or "2023-01-11",
                "transfer_type": dtype
            })
            hist_counter += 1
        geojson_features.append({
            "type": "Feature",
            "id": f"SYN-PARCEL-{rid}",
            "properties": {
                "survey_number": snum,
                "owner_name": oname or "Unspecified",
                "land_area_acres": area,
                "village": vill,
                "mandal": mand,
                "district": "Ranga Reddy",
                "state": "Telangana",
                "risk_level": "MEDIUM",
                "conflict_status": "Incomplete Record Data"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[78.34, 17.37], [78.342, 17.371], [78.343, 17.368], [78.34, 17.368], [78.34, 17.37]]]
            }
        })

    # C.6 Missing / Broken Title Chains (SYN-REC-099 to SYN-REC-100)
    # SYN-REC-099: Executant missing from prior chain
    land_records.append({
        "record_id": "SYN-REC-099",
        "owner_name": "Dharma Teja Indukuri",
        "survey_number": "SYN-904/D",
        "land_area_acres": "3.50",
        "village": "Shankarpally",
        "mandal": "Shankarpally",
        "district": "Ranga Reddy",
        "state": "Telangana",
        "registration_number": "SYN-REG-2022-1099",
        "registration_date": "2022-04-18",
        "document_type": "Sale Deed"
    })
    ownership_history.append({
        "history_id": f"SYN-HIST-{hist_counter:03d}",
        "survey_number": "SYN-904/D",
        "owner_name": "Raja Rao Mantena",
        "transfer_date": "2005-06-12",
        "transfer_type": "Original Grant"
    })
    hist_counter += 1
    ownership_history.append({
        "history_id": f"SYN-HIST-{hist_counter:03d}",
        "survey_number": "SYN-904/D",
        "owner_name": "Suresh Rao Mantena",
        "transfer_date": "2018-09-20",
        "transfer_type": "Inheritance Mutation"
    })
    hist_counter += 1
    geojson_features.append({
        "type": "Feature",
        "id": "SYN-PARCEL-SYN-REC-099",
        "properties": {
            "survey_number": "SYN-904/D",
            "owner_name": "Dharma Teja Indukuri",
            "land_area_acres": 3.50,
            "village": "Shankarpally",
            "mandal": "Shankarpally",
            "district": "Ranga Reddy",
            "state": "Telangana",
            "risk_level": "MEDIUM",
            "conflict_status": "Seller Missing from Title Chain"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[78.19, 17.44], [78.192, 17.442], [78.193, 17.439], [78.19, 17.439], [78.19, 17.44]]]
        }
    })

    # SYN-REC-100: Completely zero prior history recorded in DB
    land_records.append({
        "record_id": "SYN-REC-100",
        "owner_name": "Suryanarayana Raju Penmetsa",
        "survey_number": "SYN-905/E",
        "land_area_acres": "4.80",
        "village": "Mokila",
        "mandal": "Shankarpally",
        "district": "Ranga Reddy",
        "state": "Telangana",
        "registration_number": "SYN-REG-2023-1100",
        "registration_date": "2023-07-22",
        "document_type": "Gift Deed"
    })
    # Deliberately ZERO entries in ownership_history for SYN-905/E!
    geojson_features.append({
        "type": "Feature",
        "id": "SYN-PARCEL-SYN-REC-100",
        "properties": {
            "survey_number": "SYN-905/E",
            "owner_name": "Suryanarayana Raju Penmetsa",
            "land_area_acres": 4.80,
            "village": "Mokila",
            "mandal": "Shankarpally",
            "district": "Ranga Reddy",
            "state": "Telangana",
            "risk_level": "MEDIUM",
            "conflict_status": "Zero Historical Title Chain"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[78.21, 17.41], [78.213, 17.412], [78.214, 17.408], [78.21, 17.408], [78.21, 17.41]]]
        }
    })

    assert len(land_records) == 100, f"Expected 100 records, got {len(land_records)}"
    print(f"Total synthetic land records generated: {len(land_records)}")
    print(f"Total synthetic ownership history records generated: {len(ownership_history)}")
    print(f"Total synthetic GeoJSON features generated: {len(geojson_features)}")

    # 1. Write synthetic_land_records_100.csv
    csv_land_path = os.path.join(SAMPLE_DATA_DIR, "synthetic_land_records_100.csv")
    fieldnames_land = [
        "record_id", "owner_name", "survey_number", "land_area_acres", "village",
        "mandal", "district", "state", "registration_number", "registration_date", "document_type"
    ]
    with open(csv_land_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_land)
        writer.writeheader()
        writer.writerows(land_records)
    print(f"Written {csv_land_path}")

    # 2. Write synthetic_ownership_history_100.csv
    csv_hist_path = os.path.join(SAMPLE_DATA_DIR, "synthetic_ownership_history_100.csv")
    fieldnames_hist = ["history_id", "survey_number", "owner_name", "transfer_date", "transfer_type"]
    with open(csv_hist_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_hist)
        writer.writeheader()
        writer.writerows(ownership_history)
    print(f"Written {csv_hist_path}")

    # 3. Write parcels_synthetic_100.geojson
    geojson_path = os.path.join(SAMPLE_DATA_DIR, "parcels_synthetic_100.geojson")
    geojson_doc = {
        "type": "FeatureCollection",
        "name": "LandGuard_Synthetic_100_Parcels",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": geojson_features
    }
    with open(geojson_path, "w", encoding="utf-8") as f:
        json.dump(geojson_doc, f, indent=2)
    print(f"Written {geojson_path}")

    # 4. Write database/seed_synthetic_100.sql
    sql_path = os.path.join(DATABASE_DIR, "seed_synthetic_100.sql")
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- ====================================================================\n")
        f.write("-- LandGuard Synthetic 100 Records Baseline Seed Migration\n")
        f.write("-- 100 Fully Synthetic Records (70 Normal, 10 Duplicate, 20 Anomaly)\n")
        f.write("-- ====================================================================\n\n")
        
        f.write("-- 1. Insert Synthetic Land Records\n")
        f.write("INSERT INTO land_records (record_id, owner_name, survey_number, land_area_acres, village, mandal, district, state, registration_number, registration_date, document_type)\nVALUES\n")
        
        land_value_strs = []
        for r in land_records:
            owner_val = f"'{r['owner_name'].replace("'", "''")}'" if r['owner_name'] else "NULL"
            reg_num_val = f"'{r['registration_number'].replace("'", "''")}'" if r['registration_number'] else "NULL"
            reg_date_val = f"'{r['registration_date']}'" if r['registration_date'] else "NULL"
            row_str = f"('{r['record_id']}', {owner_val}, '{r['survey_number']}', {r['land_area_acres']}, '{r['village']}', '{r['mandal']}', '{r['district']}', '{r['state']}', {reg_num_val}, {reg_date_val}, '{r['document_type']}')"
            land_value_strs.append(row_str)
        
        f.write(",\n".join(land_value_strs))
        f.write("\nON CONFLICT (record_id) DO NOTHING;\n\n")

        f.write("-- 2. Insert Synthetic Ownership History\n")
        f.write("INSERT INTO ownership_history (history_id, survey_number, owner_name, transfer_date, transfer_type)\nVALUES\n")
        
        hist_value_strs = []
        for h in ownership_history:
            date_val = f"'{h['transfer_date']}'" if h['transfer_date'] else "NULL"
            owner_val = f"'{h['owner_name'].replace("'", "''")}'"
            type_val = f"'{h['transfer_type'].replace("'", "''")}'"
            row_str = f"('{h['history_id']}', '{h['survey_number']}', {owner_val}, {date_val}, {type_val})"
            hist_value_strs.append(row_str)

        f.write(",\n".join(hist_value_strs))
        f.write("\nON CONFLICT (history_id) DO NOTHING;\n")

    print(f"Written {sql_path}")

if __name__ == "__main__":
    generate_dataset()

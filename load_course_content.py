#!/usr/bin/env python3
import os
import sys
from csv import reader, field_size_limit
from datetime import datetime
from sqlite3 import connect, Error

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_NAME = "dump_coursera_partial.sqlite3"
DB_FILE = os.path.join(DIR_PATH, DB_NAME)
DATA_PATH = os.path.join(DIR_PATH, "data")
COURSES = [
    "agile_planning_for_software_products",
    "client_needs_and_software_requirements",
    "design_patterns",
    "introduction_to_software_product_management",
    "object_oriented_design",
    "reviews_and_metrics_for_software_improvements",
    "service_oriented_architecture",
    "software_architecture",
    "software_processes_and_agile_practices",
    "software_product_management_capstone"
]
CSV_KWARGS = {
    "delimiter": ",",
    "quotechar": "\"",
    "escapechar": "\\"
}


def create_database(conn):
    """create necessary database tables"""
    sql_create_courses = """
    CREATE TABLE IF NOT EXISTS courses (
        course_id VARCHAR(50),
        course_slug VARCHAR(2000),
        course_name VARCHAR(2000),
        course_launch_ts DATETIME,
        course_update_ts DATETIME,
        course_deleted BOOLEAN,
        course_graded BOOLEAN,
        course_desc VARCHAR(10000),
        course_restricted BOOLEAN,
        course_verification_enabled_at_ts DATETIME,
        primary_translation_equivalent_course_id VARCHAR(50),
        course_preenrollment_ts DATETIME,
        course_workload VARCHAR(100),
        course_session_enabled_ts DATETIME,
        course_promo_photo_s3_bucket VARCHAR(255),
        course_promo_photo_s3_key VARCHAR(10000),
        course_level VARCHAR(50),
        course_planned_launch_date_text VARCHAR(255),
        course_header_image_s3_bucket VARCHAR(255),
        course_header_image_s3_key VARCHAR(10000),
        PRIMARY KEY (course_id)
    )"""

    sql_create_course_branches = """
    CREATE TABLE IF NOT EXISTS course_branches (
        course_id VARCHAR(50),
        course_branch_id VARCHAR(50),
        course_branch_changes_description VARCHAR(65535),
        authoring_course_branch_name VARCHAR(255),
        authoring_course_branch_created_ts DATETIME,
        PRIMARY KEY (course_id, course_branch_id)
    )"""

    sql_create_course_branch_items = """
    CREATE TABLE IF NOT EXISTS course_branch_items (
        course_branch_id VARCHAR(255),
        course_item_id VARCHAR(255),
        course_lesson_id VARCHAR(255),
        course_branch_item_order INT8,
        course_item_type_id INT8,
        course_branch_item_name VARCHAR(255),
        course_branch_item_optional BOOLEAN,
        atom_id VARCHAR(255),
        atom_version_id INT8,
        course_branch_atom_is_frozen BOOLEAN,
        PRIMARY KEY (course_branch_id, course_item_id)
    )"""

    sql_create_course_item_types = """
    CREATE TABLE IF NOT EXISTS course_item_types (
        course_item_type_id INT8,
        course_item_type_desc VARCHAR(255),
        course_item_type_category VARCHAR(255),
        course_item_type_graded BOOLEAN,
        atom_content_type_id INT8,
        PRIMARY KEY (course_item_type_id)
    )"""

    c = conn.cursor()

    c.execute(sql_create_courses)
    c.execute(sql_create_course_branches)
    c.execute(sql_create_course_item_types)
    c.execute(sql_create_course_branch_items)

    conn.commit()


def load_data_from_csv(csv_path, conn, tbl_name):
    c = conn.cursor()
    with open(csv_path) as csvfile:
        csv_reader = reader(csvfile, **CSV_KWARGS)
        headers = next(csv_reader)
        for line in csv_reader:
            q_s = ",".join(["?", ] * len(line))
            c.execute(
                f"INSERT OR REPLACE INTO {tbl_name} VALUES ({q_s})", line)
    conn.commit()


def load_course_data(course_data_path, conn):
    for course_file in sorted(os.listdir(course_data_path)):
        csv_path = os.path.join(course_data_path, course_file)
        if course_file == "courses.csv":
            load_data_from_csv(csv_path, conn, "courses")
        elif course_file == "course_branches.csv":
            load_data_from_csv(csv_path, conn, "course_branches")
        elif course_file == "course_branch_items.csv":
            load_data_from_csv(csv_path, conn, "course_branch_items")
        elif course_file == "course_item_types.csv":
            load_data_from_csv(csv_path, conn, "course_item_types")


def parse_and_load_course_branch_item(course_data_path, conn, course_zip_name):
    content_path = os.path.join(course_data_path, "course_branch_item_content")
    course_slug = course_zip_name.replace("_","-")

    # almost like this is sql or something...
    sql_select_course_id = (
        "SELECT course_id, course_name FROM courses WHERE course_slug = (?)"
    )
    sql_select_course_branches = (
        "SELECT course_branch_id FROM course_branches " +
        "WHERE " +
        "course_id = (?)"
    )

    c = conn.cursor()
    c.execute(sql_select_course_id, (course_slug,))

    (course_id, course_name) = c.fetchone() # row
    c.execute(sql_select_course_branches, (str(course_id),))
    rows = c.fetchall() # row

    course_branch_ids = [branch_data[0] for branch_data in rows]

    

def main():
    conn = None
    try:
        field_size_limit(sys.maxsize)  # GHMatches csv threw error
        conn = connect(DB_FILE)

        sc_start = datetime.now()
        print(f"Started {sc_start.now()}")

        create_database(conn)

        for course in COURSES:
            print(course)
            course_data_path = os.path.join(DATA_PATH, course)
            load_course_data(course_data_path, conn)
            parse_and_load_course_branch_item(course_data_path, conn, course)
        conn.commit()

        sc_end = datetime.now()
        print(f"Ended {sc_end}")
        print(f"Elapsed: {sc_end - sc_start}")
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()

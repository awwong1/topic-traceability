#!/usr/bin/env python3
import json
import os
import sys
from csv import reader, field_size_limit
from datetime import datetime
from sqlite3 import connect, Error
from bs4 import BeautifulSoup
from gensim.parsing.preprocessing import preprocess_string


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

    sql_create_course_branch_modules = """
    CREATE TABLE IF NOT EXISTS course_branch_modules (
        course_branch_id VARCHAR(50),
        course_module_id VARCHAR(50),
        course_branch_module_order INT8,
        course_branch_module_name VARCHAR(2000),
        course_branch_module_desc VARCHAR(10000)
    )"""

    sql_create_course_branch_lessons = """
    CREATE TABLE IF NOT EXISTS course_branch_lessons (
        course_branch_id VARCHAR(50),
        course_lesson_id VARCHAR(50),
        course_module_id VARCHAR(50),
        course_branch_lesson_order INT8,
        course_branch_lesson_name VARCHAR(10000)
    );
    """

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

    sql_create_discussion_course_forums = """
    CREATE TABLE IF NOT EXISTS discussion_course_forums (
        discussion_forum_id VARCHAR(50),
        course_branch_id VARCHAR(50),
        discussion_course_forum_title VARCHAR(20000),
        discussion_course_forum_description VARCHAR(20000),
        discussion_course_forum_order INT8
    )"""

    sql_create_discussion_questions = """
    CREATE TABLE IF NOT EXISTS discussion_questions (
        discussion_question_id VARCHAR(50),
        ualberta_user_id VARCHAR(50) NOT NULL,
        discussion_question_title VARCHAR(20000),
        discussion_question_details VARCHAR(20000),
        discussion_question_context_type VARCHAR(50),
        course_id VARCHAR(50),
        course_module_id VARCHAR(50),
        course_item_id VARCHAR(50),
        discussion_forum_id VARCHAR(50),
        country_cd VARCHAR(2),
        group_id VARCHAR(50),
        discussion_question_created_ts DATETIME,
        discussion_question_updated_ts DATETIME
    )"""

    sql_create_discussion_answers = """
    CREATE TABLE IF NOT EXISTS discussion_answers (
        discussion_answer_id VARCHAR(50),
        ualberta_user_id VARCHAR(50) NOT NULL,
        course_id VARCHAR(50),
        discussion_answer_content VARCHAR(20000),
        discussion_question_id VARCHAR(50),
        discussion_answer_parent_discussion_answer_id VARCHAR(50),
        discussion_answer_created_ts DATETIME,
        discussion_answer_updated_ts DATETIME
    )"""

    c = conn.cursor()

    c.execute(sql_create_courses)
    c.execute(sql_create_course_branches)
    c.execute(sql_create_course_branch_modules)
    c.execute(sql_create_course_branch_lessons)
    c.execute(sql_create_course_item_types)
    c.execute(sql_create_course_branch_items)
    c.execute(sql_create_discussion_course_forums)
    c.execute(sql_create_discussion_questions)
    c.execute(sql_create_discussion_answers)

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
        elif course_file == "course_branch_modules.csv":
            load_data_from_csv(csv_path, conn, "course_branch_modules")
        elif course_file == "course_branch_lessons.csv":
            load_data_from_csv(csv_path, conn, "course_branch_lessons")
        elif course_file == "course_branch_items.csv":
            load_data_from_csv(csv_path, conn, "course_branch_items")
        elif course_file == "course_item_types.csv":
            load_data_from_csv(csv_path, conn, "course_item_types")
        elif course_file == "discussion_course_forums.csv":
            load_data_from_csv(csv_path, conn, "discussion_course_forums")
        elif course_file == "discussion_questions.csv":
            load_data_from_csv(csv_path, conn, "discussion_questions")
        elif course_file == "discussion_answers.csv":
            load_data_from_csv(csv_path, conn, "discussion_answers")


def parse_and_load_course_branch_item(course_data_path, conn, course_zip_name):
    """take all of the course branch item content and create vocabulary
    """
    content_path = os.path.join(course_data_path, "course_branch_item_content")
    course_slug = course_zip_name.replace("_", "-")

    sql_select_course_id = (
        "SELECT DISTINCT course_branch_items.course_branch_id, " +
        "course_item_id, course_branch_module_name, " +
        "course_branch_lesson_name, course_branch_item_name FROM " +
        "course_branch_modules, course_branch_lessons, course_branch_items, " +
        "course_branches, courses WHERE course_slug = (?) " +
        "AND courses.course_id == course_branches.course_id " +
        "AND course_branches.course_branch_id == course_branch_items.course_branch_id " +
        "AND course_branch_items.course_lesson_id == course_branch_lessons.course_lesson_id " +
        "AND course_branch_lessons.course_module_id == course_branch_modules.course_module_id"
    )

    c = conn.cursor()
    c.execute(sql_select_course_id, (course_slug,))

    # module name > lesson name > item name > to processed vocabulary (list of words)
    course_vocabulary = {}

    rows = c.fetchmany()
    while rows:
        for row in rows:
            (course_branch_id, course_item_id, course_branch_module_name,
             course_branch_lesson_name, course_branch_item_name,) = row
            # load the raw json file for branch item
            course_branch_item_path = os.path.join(
                content_path, "{}-{}.json".format(course_branch_id, course_item_id))
            with open(course_branch_item_path, "r") as cbif:
                # attempt to load the json file, otherwise continue
                try:
                    raw_cbi = json.load(cbif)
                except Exception as e:
                    print(e)
                    continue

                try:
                    if raw_cbi["message"] == "" and raw_cbi["statusCode"] == 204 and raw_cbi["reason"] == "ignore assesments":
                        continue
                except KeyError:
                    pass

                try:
                    if raw_cbi["message"] == "" and raw_cbi["statusCode"] == 404:
                        continue
                except KeyError:
                    pass

                try:
                    if raw_cbi["message"] == None and raw_cbi["errorCode"] == "Not Authorized":
                        continue
                except KeyError:
                    pass

                try:
                    if raw_cbi["message"].startswith("No item ItemId(") and raw_cbi["errorCode"] == None:
                        continue
                except KeyError:
                    pass

                normalized_processed_text = None

                try:
                    # try to get the definition value of the item
                    definition_raw_html = raw_cbi["linked"]["openCourseAssets.v1"][0]["definition"]["value"]
                    definition_text = " ".join(BeautifulSoup(
                        definition_raw_html, "html.parser").stripped_strings)
                    normalized_processed_text = preprocess_string(
                        definition_text)
                    update_course_vocabulary(
                        course_vocabulary, course_branch_module_name,
                        course_branch_lesson_name, course_branch_item_name,
                        normalized_processed_text)
                    continue
                except KeyError:
                    pass

                try:
                    # check if the branch item is a video with subtitles, get subtitles
                    subtitles_lookup = raw_cbi["linked"]["onDemandVideos.v1"][0]["subtitlesTxt"]
                    if not subtitles_lookup.keys():
                        continue  # no subtitles for the video
                    subtitle_filepath = course_branch_item_path + ".subtitles.txt"
                    with open(subtitle_filepath, "r") as subfp:
                        subtitle_raw_text = "".join(subfp.readlines())
                        normalized_processed_text = preprocess_string(
                            subtitle_raw_text)
                    update_course_vocabulary(
                        course_vocabulary, course_branch_module_name,
                        course_branch_lesson_name, course_branch_item_name,
                        normalized_processed_text)
                    continue
                except KeyError:
                    pass

                raise Error("unhandled cbi")

        rows = c.fetchmany()

    # save the course_vocabulary to disk
    vocab_filepath = os.path.join(
        course_data_path, "..", "vocabulary.{}.json".format(course_slug))
    with open(vocab_filepath, "w") as vocab_file:
        json.dump(course_vocabulary, vocab_file)


def update_course_vocabulary(course_vocabulary, course_branch_module_name, course_branch_lesson_name, course_branch_item_name, normalized_processed_text):
    course_branch_module = course_vocabulary.get(course_branch_module_name, {})
    course_branch_lesson = course_branch_module.get(
        course_branch_lesson_name, {})
    course_branch_item = course_branch_lesson.get(course_branch_item_name, [])
    course_branch_item.extend(normalized_processed_text)

    course_branch_lesson[course_branch_item_name] = course_branch_item
    course_branch_module[course_branch_lesson_name] = course_branch_lesson
    course_vocabulary[course_branch_module_name] = course_branch_module


def parse_and_load_discussion_questions(course_data_path, conn, course_zip_name):
    """load, parse, process discussion questions
    """
    course_slug = course_zip_name.replace("_", "-")
    sql_select_discussion_question = (
        "SELECT discussion_question_id, discussion_question_title, " +
        "discussion_question_details " +
        "FROM discussion_questions, courses WHERE " +
        "discussion_questions.course_id == courses.course_id AND " +
        "courses.course_slug == (?)"
    )

    c = conn.cursor()
    c.execute(sql_select_discussion_question, (course_slug,))

    course_questions = {}

    rows = c.fetchmany()
    while rows:
        for row in rows:
            question_id, question_title, question_details = row
            course_questions[question_id] = (
                preprocess_string(question_title) +
                preprocess_string(question_details)
            )
        rows = c.fetchmany()

    # save the course_questions to disk
    questions_filepath = os.path.join(
        course_data_path, "..", "questions.{}.json".format(course_slug))
    with open(questions_filepath, "w") as questions_file:
        json.dump(course_questions, questions_file)


def parse_and_load_discussion_answers(course_data_path, conn, course_zip_name):
    """load, parse, process discussion answers
    """
    course_slug = course_zip_name.replace("_", "-")
    sql_select_discussion_answer = (
        "SELECT discussion_answer_id, discussion_answer_content " +
        "FROM discussion_answers, courses WHERE " +
        "discussion_answers.course_id == courses.course_id AND " +
        "courses.course_slug == (?)"
    )

    c = conn.cursor()
    c.execute(sql_select_discussion_answer, (course_slug,))

    course_answers = {}

    rows = c.fetchmany()
    while rows:
        for row in rows:
            answer_id, answer_content = row
            course_answers[answer_id] = preprocess_string(answer_content)
        rows = c.fetchmany()

    # save the course_answers to disk
    answers_filepath = os.path.join(
        course_data_path, "..", "answers.{}.json".format(course_slug))
    with open(answers_filepath, "w") as answers_file:
        json.dump(course_answers, answers_file)


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
            parse_and_load_discussion_questions(course_data_path, conn, course)
            parse_and_load_discussion_answers(course_data_path, conn, course)
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

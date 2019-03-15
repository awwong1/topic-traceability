#!/usr/bin/env python3
import os
import json
import pickle
from PyInquirer import prompt, Separator
from sqlite3 import connect, Error


DIR_PATH = os.path.dirname(os.path.realpath(__file__))
DB_NAME = "dump_coursera_partial.sqlite3"
DB_FILE = os.path.join(DIR_PATH, DB_NAME)

COURSE_NAME_STUBS = [
    "agile-planning-for-software-products",
    "client-needs-and-software-requirements",
    "design-patterns",
    "introduction-to-software-product-management",
    "object-oriented-design",
    "reviews-and-metrics-for-software-improvements",
    "service-oriented-architecture",
    "software-architecture",
    "software-processes-and-agile-practices",
    "software-product-management-capstone",
]


def setup_course_inquire(course_name):
    model_res_fp = os.path.join(
        DIR_PATH, "data", "model_res.{}.json".format(course_name))
    results_fp = os.path.join(
        DIR_PATH, "data", "eval.{}.pkl".format(course_name))
    man_label_fp = os.path.join(
        DIR_PATH, "data", "manual_label.{}.json".format(course_name))

    with open(results_fp, "rb") as rf:
        course_results = pickle.load(rf)
    with open(model_res_fp, "r") as mf:
        course_model_results = json.load(mf)
    label_results = {}
    if os.path.isfile(man_label_fp):
        with open(man_label_fp, "r") as lf:
            label_results = json.load(lf)

    conn = None
    try:
        conn = connect(DB_FILE)
        inquire_course(course_name, label_results,
                       course_results, course_model_results, conn)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def inquire_course(course_name, label_results,
                   course_results, course_model_results, conn):
    print()
    pass


def main():
    course_choices = []
    course_choices.extend(COURSE_NAME_STUBS)
    course_choices.append(Separator())
    course_choices.append("abort")

    while True:
        questions = [{
            "type": "list",
            "name": "eval_course",
            "message": "Which course to manually label?",
            "choices": course_choices
        }]
        answers = prompt(questions)
        course_to_eval = answers.get("eval_course", None)
        if not course_to_eval or course_to_eval == "abort":
            return
        setup_course_inquire(course_name=course_to_eval)


if __name__ == "__main__":
    main()

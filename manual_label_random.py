#!/usr/bin/env python3
import os
import json
import pickle
from PyInquirer import prompt, Separator
from sqlite3 import connect, Error
import xml.dom.minidom


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
                       course_results, course_model_results, conn, man_label_fp)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


def inquire_questions(course_name, label_results,
                      course_results, course_model_results, conn, man_label_fp):
    label_tree = {}
    for doc_id, v in course_model_results.get("docid_to_labels", {}).items():
        s_module, s_lesson, s_item = v
        b_module = label_tree.get(s_module, {})
        b_lesson = b_module.get(s_lesson, {})
        b_item = b_lesson.get(s_item, -1)
        b_item = doc_id
        b_lesson[s_item] = b_item
        b_module[s_lesson] = b_lesson
        label_tree[s_module] = b_module

    sql_select_discussion_questions = (
        "SELECT discussion_question_id, discussion_question_title, "
        "discussion_question_details FROM " +
        "discussion_questions, courses WHERE " +
        "courses.course_slug == (?) AND " +
        "courses.course_id == discussion_questions.course_id ORDER BY RANDOM()"
    )
    c = conn.cursor()
    c.execute(sql_select_discussion_questions, (course_name, ))
    rows = c.fetchmany()
    while rows:
        for row in rows:
            question_id, question_title, question_details = row

            while True:
                if question_id in label_results.get("questions", {}):
                    prior_label_id = label_results.get(
                        "questions", {}).get(question_id, None)
                    prior_label_l = course_model_results.get(
                        "docid_to_labels").get(prior_label_id, [])
                    prior_label_str = " > ".join(prior_label_l)
                    if prior_label_id is not None and not prior_label_str:
                        prior_label_str = "unlabelable"
                    print("Already labelled as '{}'".format(prior_label_str))

                print("TITLE: {}".format(question_title))
                dom = xml.dom.minidom.parseString(question_details)
                print(dom.toprettyxml(indent=" "))

                # label module
                inq_module_choices = list(label_tree.keys())
                inq_module_choices.extend(
                    [Separator(), "skip", "unlabelable", "back"])
                inquiry_module = [{
                    "type": "list",
                    "name": "s_module",
                    "message": "Choose Course Module:",
                    "choices": inq_module_choices
                }]
                answers = prompt(inquiry_module)
                s_module = answers.get("s_module", None)
                if s_module is None:
                    exit()
                elif s_module == "skip":
                    break
                elif s_module == "unlabelable":
                    lq_results = label_results.get("questions", {})
                    lq_results[question_id] = -1  # unlabelable
                    label_results["questions"] = lq_results
                    with open(man_label_fp, "w"):
                        json.dump(label_results)
                elif s_module == "back":
                    return

                # label lesson
                inq_lesson_choices = list(label_tree[s_module].keys())
                inq_lesson_choices.extend([Separator(), "back"])
                inquiry_lesson = [{
                    "type": "list",
                    "name": "s_lesson",
                    "message": "Choose Course Lesson:",
                    "choices": inq_lesson_choices
                }]
                answers = prompt(inquiry_lesson)
                s_lesson = answers.get("s_lesson", None)
                if s_lesson is None:
                    exit()
                elif s_lesson == "back":
                    continue

                # label item
                inq_item_choices = label_tree[s_module][s_lesson]
                inq_item_choices.extend([Separator(), "back"])
                inquiry_item = [{
                    "type": "list",
                    "name": "s_item",
                    "message": "Choose Course Item:",
                    "choices": inq_item_choices
                }]
                answers = prompt(inquiry_item)
                s_item == answers.get("s_item", None)
                if s_item is None:
                    exit()
                elif s_item == "back":
                    continue
                
                

        rows = c.fetchmany()


def inquire_course(course_name, label_results,
                   course_results, course_model_results, conn, man_label_fp):
    question_labelled = label_results.get("questions", {})
    answer_labelled = label_results.get("answers", {})

    print("Labelled {}/{} questions.".format(len(question_labelled),
                                             len(course_results["question_results"])))
    print("Labelled {}/{} answers.".format(len(answer_labelled),
                                           len(course_results["answer_results"])))
    inquiry_choices = [
        "questions",
        "answers",
        Separator(),
        "back"
    ]
    inquiry_questions = [{
        "type": "list",
        "name": "q_or_a",
        "message": "Label questions or answers?",
        "choices": inquiry_choices
    }]
    answers = prompt(inquiry_questions)
    q_or_a = answers.get("q_or_a", None)
    if not q_or_a:
        exit()
    elif q_or_a == "questions":
        inquire_questions(course_name, label_results,
                          course_results, course_model_results, conn, man_label_fp)
    elif q_or_a == "answers":
        # inquire_answers()
        pass
    # default return back


def main():
    course_choices = []
    course_choices.extend(COURSE_NAME_STUBS)
    course_choices.append(Separator())
    course_choices.append("abort")

    while True:
        inquiry_questions = [{
            "type": "list",
            "name": "eval_course",
            "message": "Which course to manually label?",
            "choices": course_choices
        }]
        answers = prompt(inquiry_questions)
        course_to_eval = answers.get("eval_course", None)
        if not course_to_eval or course_to_eval == "abort":
            return
        setup_course_inquire(course_name=course_to_eval)


if __name__ == "__main__":
    main()

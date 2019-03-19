#!/usr/bin/env python3
import os
import json
import pickle
from PyInquirer import prompt, Separator
from sqlite3 import connect, Error
import xml.dom.minidom
from gensim.parsing.preprocessing import preprocess_string


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


def evaluate_course(course_name, label_results,
                      course_results, course_model_results, conn, man_label_fp):
    label_tree = {}
    for doc_id, v in course_model_results.get("docid_to_labels", {}).items():
        s_module, s_lesson, s_item = v
        b_module = label_tree.get(s_module, {})
        b_lesson = b_module.get(s_lesson, {})
        b_item = b_lesson.get(s_item, doc_id)
        b_lesson[s_item] = b_item
        b_module[s_lesson] = b_lesson
        label_tree[s_module] = b_module

    sql_select_discussion_questions = (
        "SELECT DISTINCT discussion_question_id, discussion_question_title, "
        "discussion_question_details FROM " +
        "discussion_questions, courses WHERE " +
        "courses.course_slug == (?) AND " +
        "courses.course_id == discussion_questions.course_id " +
        "ORDER BY discussion_question_created_ts"
    )
    c = conn.cursor()
    c.execute(sql_select_discussion_questions, (course_name, ))
    rows = c.fetchmany()
    while rows:
        for row in rows:
            os.system("clear")
            question_id, question_title, question_details = row
            try:
                print("Discussion Title: {}".format(question_title))
                dom = xml.dom.minidom.parseString(question_details)
                print(dom.toprettyxml(indent="  "), end="")

                tfidf_id, tfidf_score = course_model_results["questions_topic_mapping"]["cosine"][question_id]["tfidf_rank"][0]
                print("TF-IDF \tsuggested: (cos_sim: {})\n{}".format(tfidf_score, " > ".join(course_model_results["docid_to_labels"][str(tfidf_id)])))
                llda_id, llda_score = course_model_results["questions_topic_mapping"]["cosine"][question_id]["llda_rank"][0]
                print("L-LDA \tsuggested: (cos_sim: {})\n{}".format(llda_score, " > ".join(course_model_results["docid_to_labels"][str(llda_id)])))
                hdp_id, hdp_score = course_model_results["questions_topic_mapping"]["cosine"][question_id]["hdp_rank"][0]
                print("HDP-LDA\tsuggested: (cos_sim: {})\n{}".format(hdp_score, " > ".join(course_model_results["docid_to_labels"][str(hdp_id)])))
                lda_id, lda_score = course_model_results["questions_topic_mapping"]["cosine"][question_id]["lda_rank"][0]
                print("LDA \tsuggested: (cos_sim: {})\n{}".format(lda_score, " > ".join(course_model_results["docid_to_labels"][str(lda_id)])))
                at_id, at_score = course_model_results["questions_topic_mapping"]["cosine"][question_id]["atm_rank"][0]
                print("AT \tsuggested: (cos_sim: {})\n{}".format(at_score, " > ".join(course_model_results["docid_to_labels"][str(at_id)])))

            except Exception as e:
                print(e)
                pass
            input()


        rows = c.fetchmany()
    print("No more values to label!")



def main():
    course_name = "agile-planning-for-software-products"
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
        try:
            with open(man_label_fp, "r") as lf:
                label_results = json.load(lf)
        except json.decoder.JSONDecodeError:
            os.remove(man_label_fp)

    conn = None
    try:
        conn = connect(DB_FILE)
        evaluate_course(course_name, label_results,
                       course_results, course_model_results, conn, man_label_fp)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()

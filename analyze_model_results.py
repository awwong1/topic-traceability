#!/usr/bin/env python3
import os
from datetime import datetime
from numpy import ravel
from pickle import load
from json import dump
from scipy.spatial.distance import cosine, euclidean

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def analyze_course_results(course_name, course_results):
    t_start = datetime.now()
    print("ANALYZING {} ({})".format(course_name, t_start))
    docid_to_labels = invert_mapping(course_results["mapping"])

    material_results = course_results["material_results"]
    question_results = course_results["question_results"]
    answer_results = course_results["answer_results"]

    # question_id: { atm: [(doc, distance)], hdp: [(doc, distance)]}
    questions_topic_mapping = { }
    distance_functions = {
        "cosine": (cosine, True),  # function, reverse
        # "euclidean": (euclidean, False)
    }
    for key in distance_functions.keys():
        questions_topic_mapping[key] = {}

    for question_id, question_result in question_results.items():
        all_words = question_result["all_words"]
        unutilized_words = question_result["unutilized_words"]
        atm, hdp, lda, llda = flatten_gammas(question_result)

        for dist_func_name, distance_options in distance_functions.items():
            distance_function, sort_reverse = distance_options
            question_topic_map = {
                "atm_rank": [],
                "hdp_rank": [],
                "lda_rank": [],
                "llda_rank": []
            }

            for doc_id, material_result in material_results.items():
                m_atm, m_hdp, m_lda, m_llda = flatten_gammas(material_result)
                question_topic_map["atm_rank"].append((
                    doc_id,
                    distance_function(atm, m_atm)
                ))
                question_topic_map["hdp_rank"].append((
                    doc_id,
                    distance_function(hdp, m_hdp)
                ))
                question_topic_map["lda_rank"].append((
                    doc_id,
                    distance_function(lda, m_lda)
                ))
                question_topic_map["llda_rank"].append((
                    doc_id,
                    distance_function(llda, m_llda)
                ))

            question_topic_map["atm_rank"].sort(
                key=lambda tup: tup[1], reverse=sort_reverse)
            question_topic_map["hdp_rank"].sort(
                key=lambda tup: tup[1], reverse=sort_reverse)
            question_topic_map["lda_rank"].sort(
                key=lambda tup: tup[1], reverse=sort_reverse)
            question_topic_map["llda_rank"].sort(
                key=lambda tup: tup[1], reverse=sort_reverse)

        print("\rq: {}/{} (e: {})".format(
            len(questions_topic_mapping[dist_func_name]),
            len(question_results),
            datetime.now() - t_start), end="")

    model_res_fp = os.path.join(
        DIR_PATH, "data", "model_res.{}.json".format(course_name))
    with open(model_res_fp, "w") as mf:
        dump({
            "docid_to_labels": docid_to_labels,
            "questions_topic_mapping": questions_topic_mapping
        }, mf)
    print()


def flatten_gammas(result):
    atm = ravel(result["atm"])
    hdp = ravel(result["hdp"])
    lda = ravel(result["lda"])
    llda = ravel(result["llda"])
    return atm, hdp, lda, llda


def invert_mapping(mapping):
    """document to hierarchy labels.
    [modules, lessons, items]
    """
    inverted_mapping = {}
    for coursera_item_type, value_dict in mapping.items():
        # coursera_item_type one of [modules, lessons, items]
        for item_name, doc_ids in value_dict.items():
            for doc_id in doc_ids:
                doc_type = inverted_mapping.get(doc_id, [None, None, None])
                if coursera_item_type == "items":
                    doc_type[2] = item_name
                elif coursera_item_type == "lessons":
                    doc_type[1] = item_name
                elif coursera_item_type == "modules":
                    doc_type[0] = item_name
                else:
                    raise NotImplementedError(coursera_item_type)
                inverted_mapping[doc_id] = doc_type
    return inverted_mapping


def main():
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
    for course_name in COURSE_NAME_STUBS:
        results_fp = os.path.join(DIR_PATH, "data", "eval.{}.pkl".format(
            course_name))
        course_results = None
        with open(results_fp, "rb") as rf:
            course_results = load(rf)

        analyze_course_results(course_name, course_results)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Calculate distances using the topic models on the course material/discussion
posts feature vectors.
"""
import os
import numpy as np
from datetime import datetime
from numpy import ravel
from pickle import load
from json import dump
from scipy.spatial.distance import cosine, euclidean
from gensim.models import TfidfModel
from collections import Counter

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def analyze_course_results(course_name, course_results, idf_vec_size):
    t_start = datetime.now()
    print("ANALYZING {} ({})".format(course_name, t_start))
    docid_to_labels = invert_mapping(course_results["mapping"])

    material_results = course_results["material_results"]
    question_results = course_results["question_results"]
    answer_results = course_results["answer_results"]

    # question_id: { atm: [(doc, distance)], hdp: [(doc, distance)]}
    questions_topic_mapping = {}
    answers_topic_mapping = {}
    distance_functions = {
        "cosine": (cosine, False),  # function, reverse
        # "euclidean": (euclidean, False)
    }
    for key in distance_functions.keys():
        questions_topic_mapping[key] = {}
        answers_topic_mapping[key] = {}

    course_unutilized_words = []
    discussion_words = set()

    for question_id, question_result in question_results.items():
        all_words = question_result["all_words"]
        unutilized_words = question_result["unutilized_words"]
        atm, hdp, lda, llda, tfidf = flatten_gammas(question_result, idf_vec_size)

        course_unutilized_words.extend(unutilized_words)
        discussion_words = discussion_words.union(all_words)

        for dist_func_name, distance_options in distance_functions.items():
            question_topic_map = generate_topic_map(
                distance_options, material_results, atm, hdp, lda, llda, tfidf, idf_vec_size)
            questions_topic_mapping[dist_func_name][question_id] = question_topic_map

        print("\rq: {}/{} (e: {})".format(
            len(questions_topic_mapping[dist_func_name]),
            len(question_results),
            datetime.now() - t_start), end="")
    # just look at questions for time being
    # print()
    # for answer_id, answer_result in answer_results.items():
    #     all_words = question_result["all_words"]
    #     unutilized_words = question_result["unutilized_words"]
    #     atm, hdp, lda, llda, tfidf = flatten_gammas(answer_result, idf_vec_size)

    #     for dist_func_name, distance_options in distance_functions.items():
    #         answer_topic_map = generate_topic_map(
    #             distance_options, material_results, atm, hdp, lda, llda, tfidf, idf_vec_size)
    #         answers_topic_mapping[dist_func_name][answer_id] = answer_topic_map

    #     print("\ra: {}/{} (e: {})".format(
    #         len(answers_topic_mapping[dist_func_name]),
    #         len(answer_results),
    #         datetime.now() - t_start), end="")

    print()

    if True:
        # update?
        model_res_fp = os.path.join(
            DIR_PATH, "data", "model_res.{}.json".format(course_name))
        with open(model_res_fp, "w") as mf:
            dump({
                "docid_to_labels": docid_to_labels,
                "questions_topic_mapping": questions_topic_mapping,
                "answers_topic_mapping": answers_topic_mapping
            }, mf)

    unutilized_words_count = Counter(course_unutilized_words)
    ordered_unutilized_words = []
    for key, value in sorted(unutilized_words_count.items(), key=lambda x:x[1], reverse=True):
        ordered_unutilized_words.append((key, value))
    print(len(ordered_unutilized_words), len(discussion_words))
    print(ordered_unutilized_words[:5])
    forum_only_vocabulary_fp = os.path.join(
        DIR_PATH, "data", "forum_only_vocabulary.{}.json".format(course_name)
    )
    with open(forum_only_vocabulary_fp, "w") as f:
        dump(ordered_unutilized_words, f)

def generate_topic_map(distance_options, material_results, atm, hdp, lda, llda, tfidf, idf_vec_size):
    distance_function, sort_reverse = distance_options
    topic_map = {
        "atm_rank": [],
        "hdp_rank": [],
        "lda_rank": [],
        "llda_rank": [],
        "tfidf_rank": [],

        # how much better do topic models improve on tf-idf?
        "tfidf_with_atm_rank": [],
        "tfidf_with_hdp_rank": [],
        "tfidf_with_lda_rank": [],
        "tfidf_with_llda_rank": [],
    }

    for doc_id, material_result in material_results.items():
        m_atm, m_hdp, m_lda, m_llda, m_tfidf = flatten_gammas(material_result, idf_vec_size)
        topic_map["atm_rank"].append((
            doc_id,
            distance_function(atm, m_atm)
        ))
        topic_map["hdp_rank"].append((
            doc_id,
            distance_function(hdp, m_hdp)
        ))
        topic_map["lda_rank"].append((
            doc_id,
            distance_function(lda, m_lda)
        ))
        topic_map["llda_rank"].append((
            doc_id,
            distance_function(llda, m_llda)
        ))
        topic_map["tfidf_rank"].append((
            doc_id,
            distance_function(tfidf, m_tfidf)
        ))

        # Do combination of TF-IDF + four other topic models
        topic_map["tfidf_with_atm_rank"].append((
            doc_id,
            distance_function(np.concatenate((tfidf, atm)), np.concatenate((m_tfidf, m_atm)))
        ))
        topic_map["tfidf_with_hdp_rank"].append((
            doc_id,
            distance_function(np.concatenate((tfidf, hdp)), np.concatenate((m_tfidf, m_hdp)))
        ))
        topic_map["tfidf_with_lda_rank"].append((
            doc_id,
            distance_function(np.concatenate((tfidf, lda)), np.concatenate((m_tfidf, m_lda)))
        ))
        topic_map["tfidf_with_llda_rank"].append((
            doc_id,
            distance_function(np.concatenate((tfidf, llda)), np.concatenate((m_tfidf, m_llda)))
        ))



    topic_map["atm_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    topic_map["hdp_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    topic_map["lda_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    topic_map["llda_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    topic_map["tfidf_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    topic_map["tfidf_with_atm_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    topic_map["tfidf_with_hdp_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    topic_map["tfidf_with_lda_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)
    topic_map["tfidf_with_llda_rank"].sort(
        key=lambda tup: tup[1], reverse=sort_reverse)

    return topic_map


def flatten_gammas(result, idf_vec_size):
    atm = ravel(result["atm"])
    hdp = ravel(result["hdp"])
    lda = ravel(result["lda"])
    llda = ravel(result["llda"])

    tfidf_ltups = result["tfidf"]
    tfidf = np.zeros(idf_vec_size)
    for tfidf_idx, val in tfidf_ltups:
        tfidf[tfidf_idx] = val
    return atm, hdp, lda, llda, tfidf


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

        tfidf_fp = os.path.join(
            DIR_PATH, "data", "tfidf.{}.pkl".format(course_name))
        # with open(tfidf_fp, "rb") as tfidf_f:
        tfidf_model = TfidfModel.load(tfidf_fp)
        idf_vec_size = len(tfidf_model.idfs)

        analyze_course_results(course_name, course_results, idf_vec_size)


if __name__ == "__main__":
    main()

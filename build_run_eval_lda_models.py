#!/usr/bin/env python3
import os
import json
from gensim.test.utils import common_texts
from gensim.corpora.dictionary import Dictionary
from gensim.models import HdpModel, LdaModel, AuthorTopicModel
from numpy import argsort

from llda_impl import LLDA


def extract_course_texts(course_vocabulary, mapping):
    course_texts = []
    for module_name, lessons_vocabulary in course_vocabulary.items():
        for lesson_name, items_vocabulary in lessons_vocabulary.items():
            for item_name, document_words in items_vocabulary.items():
                if document_words:
                    module_mapping = mapping.get("modules", {})
                    module_map_vals = module_mapping.get(module_name, [])
                    module_map_vals.append(len(course_texts))
                    module_mapping[module_name] = module_map_vals
                    mapping["modules"] = module_mapping

                    lesson_mapping = mapping.get("lessons", {})
                    lesson_map_vals = lesson_mapping.get(lesson_name, [])
                    lesson_map_vals.append(len(course_texts))
                    lesson_mapping[lesson_name] = lesson_map_vals
                    mapping["lessons"] = lesson_mapping

                    item_mapping = mapping.get("items", {})
                    item_map_vals = item_mapping.get(item_name, [])
                    item_map_vals.append(len(course_texts))
                    item_mapping[item_name] = item_map_vals
                    mapping["items"] = item_mapping

                    course_texts.append(document_words)
    return course_texts


def build_lda_models(course_corpus, course_dictionary, mapping, course_texts):
    # ==== Train Unsupervised LDA ====
    lda_model = LdaModel(
        corpus=course_corpus,
        id2word=course_dictionary
    )

    # ==== Train Unsupervised HDP-LDA ====
    hdp_model = HdpModel(
        corpus=course_corpus,
        id2word=course_dictionary
    )

    # ==== Train Author Topic Model ====
    author_to_doc = {}  # author topic LDA (authors are modules,lessons,items)
    for author_type in ["modules", "lessons", "items"]:
        entity_to_doc = mapping[author_type]
        for entity_name, entity_docs in entity_to_doc.items():
            author_to_doc["{}: {}".format(
                author_type[0].capitalize(), entity_name)] = entity_docs
    at_model = AuthorTopicModel(
        corpus=course_corpus,
        id2word=course_dictionary,
        author2doc=author_to_doc
    )

    # ==== Train Labeled LDA ====
    # explicitly supervised, labeled LDA
    llda_alpha = 1
    llda_beta = 0.01
    llda_iterations = 50
    labels = []
    corpus = []
    labelset = set()
    for course_text_id in range(0, len(course_texts)):
        doc_labels = []
        # get module label name
        for module_name, doc_vec in mapping["modules"].items():
            if course_text_id in doc_vec:
                doc_labels.append("M: {}".format(module_name))
                break

        # get lesson label name
        for lesson_name, doc_vec in mapping["lessons"].items():
            if course_text_id in doc_vec:
                doc_labels.append("L: {}".format(lesson_name))
                break

        for item_name, doc_vec in mapping["items"].items():
            if course_text_id in doc_vec:
                doc_labels.append("I: {}".format(item_name))
                break

        labels.append(doc_labels)
        corpus.append(course_texts[course_text_id])
        labelset = labelset.union(doc_labels)

    llda_model = LLDA(llda_alpha, llda_beta, K=len(labels))
    llda_model.set_corpus(corpus, labels)
    llda_model.train(iteration=llda_iterations)

    # phi = llda.phi()
    # for k, label in enumerate(labelset):
    #     print ("\n-- label %d : %s" % (k + 1, label))
    #     for w in argsort(-phi[k + 1])[:10]:
    #         print("%s: %.4f" % (llda.vocas[w], phi[k + 1,w]))
    return lda_model, hdp_model, at_model, llda_model


def main():
    DIR_PATH = os.path.dirname(os.path.realpath(__file__))

    DATA_JSON = [
        "agile-planning-for-software-products.json",
        "client-needs-and-software-requirements.json",
        "design-patterns.json",
        "introduction-to-software-product-management.json",
        "object-oriented-design.json",
        "reviews-and-metrics-for-software-improvements.json",
        "service-oriented-architecture.json",
        "software-architecture.json",
        "software-processes-and-agile-practices.json",
        "software-product-management-capstone.json",
    ]

    # for course_name, course_vocabulary in vocabs.items():
    for course_name in DATA_JSON:
        # ==== Load the processed vocabulary into memory ==== #
        vocab_fp = os.path.join(
            DIR_PATH, "data", "vocabulary.{}".format(course_name))
        with open(vocab_fp, "r") as vf:
            # course name / module name / lesson name / item name > item
            course_vocabulary = json.load(vf)

        # ==== Generate Course Corpus, Dictionary ==== #
        mapping = {}  # holds the mapping for author topic models
        course_texts = extract_course_texts(course_vocabulary, mapping)
        course_dictionary = Dictionary(course_texts)
        course_corpus = [course_dictionary.doc2bow(
            text) for text in course_texts]

        print("BUILDING MODELS FOR {}".format(course_name))
        lda_model, hdp_model, at_model, llda_model = build_lda_models(
            course_corpus, course_dictionary,
            mapping, course_texts)

        print("EVALUATING {} FORUM ACTIVITY".format(course_name))
        question_results = {}
        question_fp = os.path.join(
            DIR_PATH, "data", "questions.{}".format(course_name))
        with open(question_fp, "r") as qf:
            # question_id > content
            course_questions = json.load(qf)
        for question_id, question_words in course_questions.items():
            # convert to gensim format for gensim models
            question_corpus = course_dictionary.doc2bow(question_words)
            chunk = (question_corpus, )
            # discussion question relation over set 100 topics
            lda_q_gamma = lda_model.inference(chunk=chunk)[0]
            # discussion question relation over capped 150 topics
            hdp_q_gamma = hdp_model.inference(chunk=chunk)

            # author to doc relation over 100 topics (each post is a new author)
            q_author2doc = {**at_model.author2doc}
            for q_author in q_author2doc.keys():
                q_author2doc[q_author] = ()
            q_author2doc[question_id] = (0, )
            at_q_gamma = at_model.inference(
                chunk=chunk,
                author2doc=q_author2doc,
                doc2author={0: (question_id,)},
                rhot=0.1
            )
            # raw text OK here
            llda_q_gamma = llda_model.inference(question_words)

            print("q")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import json
from gensim.test.utils import common_texts
from gensim.corpora.dictionary import Dictionary
from gensim.models import HdpModel, LdaModel, AuthorTopicModel
from numpy import argsort

from llda_impl import LLDA


def extract_course_texts(course_name, course_vocabulary, mapping):
    course_texts = []
    # print(course_name)
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
    )

    # ==== Train Labeled LDA ====
    # explicitly supervised, labeled LDA
    llda_alpha = 1
    llda_beta = 0.01
    llda_iterations = 100
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
        "vocabulary.agile-planning-for-software-products.json",
        "vocabulary.client-needs-and-software-requirements.json",
        "vocabulary.design-patterns.json",
        "vocabulary.introduction-to-software-product-management.json",
        "vocabulary.object-oriented-design.json",
        "vocabulary.reviews-and-metrics-for-software-improvements.json",
        "vocabulary.service-oriented-architecture.json",
        "vocabulary.software-architecture.json",
        "vocabulary.software-processes-and-agile-practices.json",
        "vocabulary.software-product-management-capstone.json",
    ]

    # course name / module name / lesson name / item name > item
    vocabs = {}

    for vocab_text_file in DATA_JSON:
        vocab_fp = os.path.join(DIR_PATH, "data", vocab_text_file)
        with open(vocab_fp, "r") as vf:
            vocab = json.load(vf)
            vocabs[vocab_text_file] = vocab

    doc_lens = []
    for course_name, course_vocabulary in vocabs.items():
        # ==== Generate Course Corpus, Dictionary ==== #
        mapping = {}  # holds the mapping for author topic models
        course_texts = extract_course_texts(
            course_name, course_vocabulary, mapping)
        course_dictionary = Dictionary(course_texts)
        course_corpus = [course_dictionary.doc2bow(
            text) for text in course_texts]
        doc_lens.extend([len(x) for x in course_texts])

        print("BUILDING MODELS FOR {}".format(course_name))
        lda_model, hdp_model, at_model, llda_model = build_lda_models(
            course_corpus, course_dictionary,
            mapping, course_texts)
        
        print("RANKING {} FORUM ACTIVITY".format(course_name))

    # print(len(doc_lens))
    # print(max(doc_lens), min(doc_lens), sum(doc_lens)/len(doc_lens))


if __name__ == "__main__":
    main()

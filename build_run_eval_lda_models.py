#!/usr/bin/env python3
import os
import json
from datetime import datetime
from gensim.test.utils import common_texts
from gensim.corpora.dictionary import Dictionary
from gensim.models import HdpModel, LdaModel, AuthorTopicModel, TfidfModel
from numpy import argsort
from pickle import dump

from llda_impl import LLDA

DIR_PATH = os.path.dirname(os.path.realpath(__file__))


def extract_course_texts_mapping(course_vocabulary):
    mapping = {}
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
    return course_texts, mapping


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
    llda_alpha = 0.01
    llda_beta = 0.001
    llda_iterations = 50
    llda_labels = []
    llda_corpus = []
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

        llda_labels.append(doc_labels)
        llda_corpus.append(course_texts[course_text_id])
        labelset = labelset.union(doc_labels)

    llda_model = LLDA(llda_alpha, llda_beta, K=len(llda_labels))
    llda_model.set_corpus(llda_corpus, llda_labels)
    llda_model.train(iteration=llda_iterations)

    # phi = llda.phi()
    # for k, label in enumerate(labelset):
    #     print ("\n-- label %d : %s" % (k + 1, label))
    #     for w in argsort(-phi[k + 1])[:10]:
    #         print("%s: %.4f" % (llda.vocas[w], phi[k + 1,w]))
    return lda_model, hdp_model, at_model, llda_model, llda_labels


def eval_answers(course_name, course_dictionary, lda_model, hdp_model, at_model, llda_model, c_start, rhot=0.1):
    answer_results = {}
    answer_fp = os.path.join(
        DIR_PATH, "data", "answers.{}.json".format(course_name))
    with open(answer_fp, "r") as af:
        course_answers = json.load(af)
    for answer_id, answer_content in course_answers.items():
        answer_corpus = course_dictionary.doc2bow(answer_content)
        chunk = (answer_corpus, )
        # discussion answer relation over set 100 topics
        lda_a_gamma = lda_model.inference(chunk=chunk)[0]
        # discussion answer relation over capped 150 topics
        hdp_a_gamma = hdp_model.inference(chunk=chunk)[0]

        # author to doc relation over 100 topics (each post is a new author)
        at_a_gamma = at_model.inference(
            chunk=chunk,
            author2doc={answer_id: (0, )},
            doc2author={0: (answer_id,)},
            rhot=rhot
        )[0]
        # raw text OK here
        llda_a_gamma = llda_model.inference(answer_content)

        answer_results[answer_id] = {
            "lda": lda_a_gamma,
            "hdp": hdp_a_gamma,
            "atm": at_a_gamma,
            "llda": llda_a_gamma,
            "all_words": answer_content,
            "unutilized_words": [w for w in answer_content if w not in course_dictionary.token2id]
        }
        print("\ra_eval {}: {}/{} (e: {})".format(
            answer_id,
            len(answer_results.keys()), len(course_answers),
            datetime.now() - c_start), end="")
    print()
    return answer_results


def eval_questions(course_name, course_dictionary, lda_model, hdp_model, at_model, llda_model, c_start, rhot=0.1):
    question_results = {}
    question_fp = os.path.join(
        DIR_PATH, "data", "questions.{}.json".format(course_name))
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
        hdp_q_gamma = hdp_model.inference(chunk=chunk)[0]

        # author to doc relation over 100 topics (each post is a new author)
        at_q_gamma = at_model.inference(
            chunk=chunk,
            author2doc={question_id: (0, )},
            doc2author={0: (question_id,)},
            rhot=rhot
        )[0]
        # raw text OK here
        llda_q_gamma = llda_model.inference(question_words)

        question_results[question_id] = {
            "lda": lda_q_gamma,
            "hdp": hdp_q_gamma,
            "atm": at_q_gamma,
            "llda": llda_q_gamma,
            "all_words": question_words,
            "unutilized_words": [w for w in question_words if w not in course_dictionary.token2id]
        }
        print("\rq_eval {}: {}/{} (e: {})".format(
            question_id,
            len(question_results.keys()), len(course_questions),
            datetime.now() - c_start), end="")
    print()
    return question_results


def eval_material(course_texts, course_corpus, lda_model, hdp_model, at_model, llda_model, c_start, rhot=0.1):
    material_results = {}
    for course_doc_idx in range(0, len(course_texts)):
        idx_course_corpus = course_corpus[course_doc_idx]
        chunk = (idx_course_corpus, )
        lda_c_gamma = lda_model.inference(chunk=chunk)[0]
        hdp_c_gamma = hdp_model.inference(chunk=chunk)[0]
        at_c_gamma = at_model.inference(
            chunk=chunk,
            author2doc=at_model.author2doc,
            doc2author=at_model.doc2author,
            rhot=rhot
        )[0]
        idx_course_texts = course_texts[course_doc_idx]
        llda_c_gamma = llda_model.inference(idx_course_texts)
        material_results[course_doc_idx] = {
            "lda": lda_c_gamma,
            "hdp": hdp_c_gamma,
            "atm": at_c_gamma,
            "llda": llda_c_gamma
        }
        print("\rc_eval {}/{} (e: {})".format(
            course_doc_idx +
            1, len(course_texts), datetime.now() - c_start), end="")
    print()
    return material_results


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

    # for course_name, course_vocabulary in vocabs.items():
    for course_name in COURSE_NAME_STUBS:
        # ==== Load the processed vocabulary into memory ==== #
        vocab_fp = os.path.join(
            DIR_PATH, "data", "vocabulary.{}.json".format(course_name))
        with open(vocab_fp, "r") as vf:
            # course name / module name / lesson name / item name > item
            course_vocabulary = json.load(vf)

        # ==== Generate Course Corpus, Dictionary ==== #
        course_texts, mapping = extract_course_texts_mapping(course_vocabulary)
        course_dictionary = Dictionary(course_texts)
        course_corpus = [course_dictionary.doc2bow(
            text) for text in course_texts]

        c_start = datetime.now()

        print("BUILDING MODELS FOR {} ({})".format(course_name, c_start))
        lda_model, hdp_model, at_model, llda_model, llda_labels = build_lda_models(
            course_corpus, course_dictionary,
            mapping, course_texts)

        # baseline TF-IDF
        tfidf_model = TfidfModel(
            corpus=course_corpus,
            id2word=course_dictionary,
        )

        print("EVALUATING FORUM ACTIVITY {} (e: {})".format(
            course_name, datetime.now() - c_start))
        material_results = eval_material(
            course_texts, course_corpus, lda_model, hdp_model, at_model, llda_model, c_start)
        question_results = eval_questions(
            course_name, course_dictionary, lda_model, hdp_model, at_model, llda_model, c_start)
        answer_results = eval_answers(
            course_name, course_dictionary, lda_model, hdp_model, at_model, llda_model, c_start)

        print("SAVING VECTORS FOR {} (e: {})".format(
            course_name, datetime.now() - c_start))
        results_fp = os.path.join(
            DIR_PATH, "data", "eval.{}.pkl".format(course_name))
        with open(results_fp, "wb") as rf:
            dump({
                "mapping": mapping,
                "material_results": material_results,
                "question_results": question_results,
                "answer_results": answer_results},
                rf)
        tfidf_fp = os.path.join(
            DIR_PATH, "data", "tfidf.{}.pkl".format(course_name))
        with open(tfidf_fp, "wb") as tfidf_f:
            tfidf_model.save(tfidf_f)

        print("{} done! (e: {})\n".format(
            course_name, datetime.now() - c_start))


if __name__ == "__main__":
    main()

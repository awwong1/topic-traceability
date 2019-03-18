#!/usr/bin/env python3
import os
import pickle
import json
import random
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
import statistics

DIR_PATH = os.path.dirname(os.path.realpath(__file__))

COURSE_NAME_STUBS = {
    "agile-planning-for-software-products": "Agile Planning for Software Products",
    "client-needs-and-software-requirements": "Client Needs and Software Requirements",
    "design-patterns": "Design Patterns",
    "introduction-to-software-product-management": "Introduction to Software Product Management",
    "object-oriented-design": "Object Oriented Design",
    "reviews-and-metrics-for-software-improvements": "Reviews and Metrics for Software Improvements",
    "service-oriented-architecture": "Service Oriented Architecture",
    "software-architecture": "Software Architecture",
    "software-processes-and-agile-practices": "Software Processes and Agile Practices",
    "software-product-management-capstone": "Software Product Management Capstone",
}

MODEL_NAME_STUBS = {
    "atm_rank": "Author-Topic",
    "hdp_rank": "HDP-LDA",
    "lda_rank": "LDA",
    "llda_rank": "Labeled LDA",
    "tfidf_rank": "TF-IDF"
}


def setup_course_plot(course_name_stub, course_name_readable):
    model_res_fp = os.path.join(
        DIR_PATH, "data", "model_res.{}.json".format(course_name_stub))
    results_fp = os.path.join(
        DIR_PATH, "data", "eval.{}.pkl".format(course_name_stub))
    man_label_fp = os.path.join(
        DIR_PATH, "data", "manual_label.{}.json".format(course_name_stub))

    with open(results_fp, "rb") as rf:
        course_results = pickle.load(rf)
    with open(model_res_fp, "r") as mf:
        course_model_results = json.load(mf)

    mmr_correct_question_labels = {}  # human labelled data or TFIDF generated
    if os.path.isfile(man_label_fp):
        try:
            with open(man_label_fp, "r") as ml_f:
                manually_labelled_questions = json.load(ml_f)["questions"]
                for mq_id, val in manually_labelled_questions.items():
                    if int(val) >= 0:
                        mmr_correct_question_labels[mq_id] = int(val)
        except:
            pass
    print("{} human labeled: {}".format(
        course_name_stub, len(mmr_correct_question_labels)))
    if len(mmr_correct_question_labels) < 100:
        return {}
    cosine_ranks = course_model_results["questions_topic_mapping"]["cosine"]

    # TEST USING LOW TFIDF SCORE AS SOURCE OF TRUTH FOR PLOTTING
    # TFID_RANK_THRESHOLD = 0.8
    # for question_id, model_rank_dict in cosine_ranks.items():
    #     top_tfid_ranks = model_rank_dict["tfidf_rank"][:3]
    #     # if top three have cosine sim > threshold, skip
    #     if max([score for (tf_idx, score) in top_tfid_ranks]) > TFID_RANK_THRESHOLD:
    #         continue
    #     mmr_correct_question_labels[question_id] = top_tfid_ranks[0][0]

    # Bootstrap sample 1000 from correct labels & calculate MRR
    chosen_questions = random.choices(
        list(mmr_correct_question_labels.keys()), k=1000)
    all_model_rrs = {}
    for qid in chosen_questions:
        correct = mmr_correct_question_labels[qid]
        model_rank_dict = cosine_ranks[qid]
        for model_name, model_rank in model_rank_dict.items():
            reciprocal_ranks = all_model_rrs.get(model_name, [])
            model_choices = [atm_choice for (atm_choice, _score) in model_rank]
            correct_idx = model_choices.index(correct)
            reciprocal_ranks.append(1/(correct_idx + 1))
            all_model_rrs[model_name] = reciprocal_ranks

    # convert to dataframe
    figure_label_model_name = "Model"
    figure_label_recip_rank = "Reciprocal Rank"
    pd_data_dict = {figure_label_model_name: [], figure_label_recip_rank: []}
    for model_name, reciprocal_ranks in all_model_rrs.items():
        # print("{} mean: {}, stdev: {}, median: {}".format(
        #     model_name,
        #     statistics.mean(reciprocal_ranks),
        #     statistics.stdev(reciprocal_ranks),
        #     statistics.median(reciprocal_ranks)
        # ))
        print("{} mean: {:.3f}".format(
            model_name,
            statistics.mean(reciprocal_ranks)
        ))

        for reciprocal_rank in reciprocal_ranks:
            pd_data_dict[figure_label_model_name].append(
                MODEL_NAME_STUBS.get(model_name, model_name))
            pd_data_dict[figure_label_recip_rank].append(reciprocal_rank)
    pd_data = pd.DataFrame(data=pd_data_dict)

    # print(pd_data.groupby("Model").mean())
    # print(pd_data.groupby("Model").std())

    # Plot the MMR box plots
    fig, ax = plt.subplots()
    x_order = ["TF-IDF", "Author-Topic", "LDA", "HDP-LDA", "Labeled LDA"]
    ax.set_title("Traceability of {}".format(course_name_readable))
    sns.set(style="whitegrid", palette="pastel")
    sns.violinplot(
        # sns.boxplot(
        x=figure_label_model_name, y=figure_label_recip_rank,
        order=x_order,
        cut=0,
        scale="width",  # area, count, width
        inner="box",  # box, quartile, point, stick, None,
        bw="scott",  # scott, silverman, float
        data=pd_data)
    for model_name, reciprocal_ranks in all_model_rrs.items():
        # draw mean on plot as line
        model_mean = statistics.mean(reciprocal_ranks)
        col = x_order.index(MODEL_NAME_STUBS.get(model_name))
        ax.hlines(
            y=model_mean,
            xmin=col - 0.1,
            xmax=col + 0.1,
            color="#663399"
            # color="#ffffff"
        )
    plt.ylim(0, 1.01)
    plt.show()

    return pd_data_dict


def main():
    random.seed(0)
    all_pd_data_dict = {
        "Course": [],
        "Model": [],
        "Reciprocal_Rank": []
    }
    for course_name_stub, course_name_readable in COURSE_NAME_STUBS.items():
         course_pd_data_dict = setup_course_plot(course_name_stub, course_name_readable)
         for k, v_list in course_pd_data_dict.items():
            if k == "Model":
                all_pd_data_dict["Course"].extend([course_name_readable] * len(v_list))
                all_pd_data_dict["Model"].extend(v_list)
            elif k == "Reciprocal Rank":
                all_pd_data_dict["Reciprocal_Rank"].extend(v_list)
    df_path = os.path.join(DIR_PATH, "final_mrr.csv")
    all_pd_data = pd.DataFrame(data=all_pd_data_dict)
    all_pd_data.to_csv(df_path)


if __name__ == "__main__":
    main()

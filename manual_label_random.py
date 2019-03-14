#!/usr/bin/env python3
import os
from PyInquirer import prompt, Separator

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
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


def inquire_course(course_name):
    
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
        course_to_eval = answers.get("course_to_eval", None)
        if not course_to_eval or course_to_eval == "abort":
            return
        inquire_course(course_name=course_to_eval)


if __name__ == "__main__":
    main()

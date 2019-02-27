#!/usr/bin/env python3
import csv
import json
import os
from requests import request


def main():
    # course_name = "agile_planning_for_software_products"
    # course_name = "client_needs_and_software_requirements"
    # course_name = "design_patterns"
    # course_name = "introduction_to_software_product_management"
    # course_name = "object_oriented_design"
    # course_name = "reviews_and_metrics_for_software_improvements"
    # course_name = "service_oriented_architecture"
    # course_name = "software_architecture"
    # course_name = "software_processes_and_agile_practices"
    course_name = "software_product_management_capstone"

    dir_path = os.path.dirname(os.path.realpath(__file__))
    cbi_path = os.path.join(
        dir_path, "data", course_name,
        "course_branch_items.csv")

    course_branch_items = []

    with open(cbi_path) as csvfile:
        reader = csv.reader(
            csvfile, delimiter=",", doublequote=True, quotechar="\"")
        headers = next(reader)
        # ['course_branch_id', 'course_item_id', 'course_lesson_id', 'course_branch_item_order', 'course_item_type_id', 'course_branch_item_name', 'course_branch_item_optional', 'atom_id', 'atom_version_id', 'course_branch_atom_is_frozen']
        for line in reader:
            course_branch_items.append((line[0], line[1], line[4]))

    # EXAMPLE PULL FROM ONDEMAND API
    # ['NpTR4zVwEeWfzhKP8GtZlQ', 'BayLT', 'Ew5Go', '1', '3', 'Meet your presenters: Morgan Patzelt', 'f', '', '', '']
    # https://www.coursera.org/api/onDemandSupplements.v1/NpTR4zVwEeWfzhKP8GtZlQ~BayLT?includes=asset&fields=openCourseAssets.v1(typeName)%2CopenCourseAssets.v1(definition)

    cbic_path = os.path.join(
        dir_path, "data", course_name, "course_branch_item_content"
    )
    if not os.path.isdir(cbic_path):
        os.mkdir(cbic_path)

    req_params = {
        "allow_redirects": True,
        "headers": {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en",
            "cache-control": "max-age=0",
            "cookie": "__204u=4804369822-1542987630497; __204r=; CSRF3-Token=1552148166.tKoGgx081YB8jLBU; CAUTH=MrFSokH5mHY0sWVewU24jTnZIg9FFciNsodm-1hTL_cbLlrzZ2uKQSlCmxxW_NJMYuB11fh0f1YKUnFH3whAWg.91zVS-uoGOBj-S9adEKlaA.dSDhAOEoL-vmDMzKX61Gbzdn35EUDhVYwkg3X1QR43XBNceHDqtLtSxlOeWu3nuIUpd8ZOOJ_HXGP5G3cU0jat2SrXhjspotT6okPapD4EfDe9KXjSYlB7gJZW7jxGn5WJy6-TwK6PNgcZcbAPbJJvJof3Wj_1O4jU8LDkc18vzbZmM4ofB3krUGFgLSn0ku; ip_origin=US; ip_currency=USD; __400v=a2e47460-f161-4b81-b40c-31e4920b398f; __400vt=1551301674369",
            "dnt": "1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.96 Safari/537.36"
        }
    }
    for course_branch_item_tup in course_branch_items:
        try:
            course_branch_id, course_item_id, course_item_type_id = course_branch_item_tup
            dump_filename = "{}-{}.json".format(
                course_branch_id, course_item_id)
            if os.path.isfile(os.path.join(cbic_path, dump_filename)):
                with open(os.path.join(cbic_path, dump_filename)) as df:
                    fetch_file = json.load(df)
                    if "message" in fetch_file and fetch_file.get("message", "") is not None and fetch_file.get("message", "").startswith("No item ItemId"):
                        continue
                    if "errorCode" in fetch_file:
                        print("\n{} contains err, refetching".format(dump_filename))
                    else:
                        # print("\nAlready fetched", dump_filename)
                        continue
            print("\rFetch ({}) {}".format(course_item_type_id, dump_filename), end="")
            if course_item_type_id in ["3", ]:
                # 3: supplement, supplement
                url = "https://www.coursera.org/api/onDemandSupplements.v1/{course_branch_id}~{course_item_id}?includes=asset&fields=openCourseAssets.v1(typeName)%2CopenCourseAssets.v1(definition)".format(
                    course_branch_id=course_branch_id,
                    course_item_id=course_item_id
                )
                r = request('get', url, **req_params)
                with open(os.path.join(cbic_path, dump_filename), "w") as f:
                    json.dump(r.json(), f)

            elif course_item_type_id in ["1", ]:
                # 1: lecture, lecture
                url = "https://www.coursera.org/api/onDemandLectureVideos.v1/{course_branch_id}~{course_item_id}?includes=video&fields=onDemandVideos.v1(sources%2Csubtitles%2CsubtitlesVtt%2CsubtitlesTxt)".format(
                    course_branch_id=course_branch_id,
                    course_item_id=course_item_id
                )
                r = request('get', url, **req_params)
                r_json = r.json()
                with open(os.path.join(cbic_path, dump_filename), "w") as f:
                    json.dump(r_json, f)
                if r_json.get("statusCode", None) == 404:
                    continue
                # {"errorCode": null, "message": "No item ItemId(CourseElementId(xwUxm)) in course", "details": null}
                if r_json.get("message", "").startswith("No item ItemId"):
                    continue

                subtitlestxt_url = r_json['linked']['onDemandVideos.v1'][0]['subtitlesTxt']['en']
                r_txt = request('get', "https://www.coursera.org" +
                                subtitlestxt_url, **req_params)
                with open(os.path.join(cbic_path, dump_filename + ".subtitles.txt"), "w") as f:
                    f.write(r_txt.text)

            elif course_item_type_id in ["4", "5", "6", "7", "12"]:
                # 4: peer, peer
                # 5: quiz, quiz
                # 6: exam, quiz
                # 7: others,
                # 12: phased peer, peer
                with open(os.path.join(cbic_path, dump_filename), "w") as f:
                    json.dump({"message": "", "statusCode": 204,
                               "reason": "ignore assesments"}, f)

            else:
                print("\nUnhandled type ", course_item_type_id)
        except Exception as e:
            print("\nCould not parse", course_branch_item_tup)
            print(e)


if __name__ == "__main__":
    main()

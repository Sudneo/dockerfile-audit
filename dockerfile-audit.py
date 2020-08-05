import os
import argparse
import logging
import json
from dockerfile import Auditor
from dockerfile import Policy
from report import report


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--policy", default="policy.yaml", help="The dockerfile policy to use for the audit.")
    parser.add_argument("-d", "--dockerfile", type=str, required=True, help="The Dockerfile to audit."
                                                                            " Can be both a file or a directory.")
<<<<<<< HEAD
    parser.add_argument("--parse-only", action='store_true', help="Simply Parse the Dockerfile(s) and return the"
                                                                  " content, without applying any policy. Only JSON "
                                                                  "report is supported for this.")
=======
>>>>>>> master
    parser.add_argument("-j", "--json", action='store_true', help="Generate a JSON file with the findings.")
    parser.add_argument("-r", "--report", action='store_true', help="Generate a PDF report about the findings.")
    parser.add_argument("-o", "--json-outfile", default="dockerfile-audit.json", help="Name of the JSON file.")
    parser.add_argument("-n", "--report-name", default="report.pdf", help="The name of the PDF report.")
    parser.add_argument("-t", "--report-template", default="templates/report-template.tex",
                        help="The template for the report to use")
    parser.add_argument("-v", "--verbose", action='store_true', help="Enables debug output")
    args = parser.parse_args()
    return args


def __audit(files_to_process, policy):
    auditor = Auditor.DockerfileAuditor(policy)
    policy_results = list()
    for file in files_to_process:
        try:
            policy_results.append(auditor.audit(file))
            logger.info(f"Scanning file: {file}")
        except Auditor.AuditException:
            pass
    return policy_results


def __parse(files_to_process):
    dockerfiles_parsed = list()
    auditor = Auditor.DockerfileAuditor()
    for file in files_to_process:
        try:
            dockerfiles_parsed.append(auditor.parse_only(file))
        except Auditor.AuditException:
            pass
    return dockerfiles_parsed


def __get_files_to_process(d_argument):
    files_to_scan = list()
    if os.path.isfile(d_argument):
        files_to_scan = [d_argument]
    elif os.path.isdir(d_argument):
        files_in_dir = sorted(os.listdir(d_argument))
        for file in files_in_dir:
            files_to_scan.append(f"{d_argument}/{file}")
        logger.info(f"Scanning {len(files_to_scan)} files in {d_argument}")
    return files_to_scan


def __get_policy():
    try:
        policy = Policy.DockerfilePolicy(arguments.policy)
        return policy
    except (FileNotFoundError, TypeError) as error:
        logger.error(error)
        exit(1)
<<<<<<< HEAD


def main():
    files_to_process = __get_files_to_process(arguments.dockerfile)
    if arguments.parse_only:
        parsed_dockerfiles = __parse(files_to_process)
        if arguments.json:
            with open(arguments.json_outfile, "w") as fp:
                json.dump(parsed_dockerfiles, indent=2, sort_keys=True, fp=fp)
    else:
        policy = __get_policy()
        policy_results = __audit(files_to_process, policy)
        if len(policy_results) == 0:
            logger.warning("No files were processed, reports will be skipped.")
        else:
            if arguments.json:
                with open(arguments.json_outfile, "w") as fp:
                    json.dump(policy_results, indent=2, sort_keys=True, fp=fp)
            if arguments.report:
                logger.debug("Preparing to generate PDF report.")
                report.generate_latex_report(policy, policy_results, arguments.report_template, arguments.report_name)
=======
    auditor = Auditor.DockerfileAuditor(policy)
    if os.path.isfile(arguments.dockerfile):
        try:
            policy_results.append(auditor.audit(arguments.dockerfile))
            logger.info(f"Scanning file: {arguments.dockerfile}")
        except Auditor.AuditException:
            pass
    elif os.path.isdir(arguments.dockerfile):
        files_to_scan = sorted(os.listdir(arguments.dockerfile))
        logger.info(f"Scanning {len(files_to_scan)} files in {arguments.dockerfile}")
        for file in files_to_scan:
            try:
                policy_results.append(auditor.audit(f"{arguments.dockerfile}/{file}"))
            except Auditor.AuditException:
                pass
    if len(policy_results) == 0:
        logger.warning("No files were processed, reports will be skipped.")
        exit(0)
    if arguments.json:
        with open(arguments.json_outfile, "w") as fp:
            json.dump(policy_results, indent=2, sort_keys=True, fp=fp)
    if arguments.report:
        logger.debug("Preparing to generate PDF report.")
        report.generate_latex_report(policy, policy_results, arguments.report_template, arguments.report_name)
>>>>>>> master


if __name__ == '__main__':
    logger = logging.getLogger()
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT)
    arguments = get_args()
    if arguments.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    main()

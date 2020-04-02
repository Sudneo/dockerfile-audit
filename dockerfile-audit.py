import os
import subprocess
import argparse
import logging
import jinja2
import json
from shutil import copyfile
from dockerfile import Dockerfile
from dockerfile import Policy


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--policy", default="policy.yaml", help="The dockerfile policy to use for the audit.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--dockerfile", type=str, help="The Dockerfile to audit.")
    group.add_argument("-b", "--batch", type=str, help="A directory in which all files will be audited.")
    parser.add_argument("-j", "--json", action='store_true', help="Generate a JSON file with the findings.")
    parser.add_argument("-r", "--report", action='store_true', help="Generate a PDF report about the findings.")
    parser.add_argument("-n", "--report-name", default="report.pdf", help="The name of the PDF report.")
    parser.add_argument("-t", "--report-template", default="templates/report-template.tex",
                        help="The template for the report to use")
    parser.add_argument("-v", "--verbose", action='store_true', help="Enables debug output")
    args = parser.parse_args()
    return args


def generate_report(policy, policy_results, template, outfile):
    logger.info("Starting report generation.")
    failure_stats = get_rules_violation_stats(policy_results, policy)
    summary_stats = get_summary_stats(policy_results)
    enabled_policy_rules = {'policy_rules_enabled': policy.get_policy_rules_enabled()}
    for enabled_rule in enabled_policy_rules['policy_rules_enabled']:
        enabled_rule['type'] = latex_escape(enabled_rule['type'])
        enabled_rule['details'] = latex_escape(enabled_rule['details'])
    for item in policy_results:
        item['filename'] = latex_escape(item['filename'])
        try:
            for rule_test in item['failed-tests']:
                for rule in rule_test:
                    rule['type'] = latex_escape(rule['type'])
                    rule['details'] = latex_escape(rule['details'])
                    rule['mitigations'] = latex_escape(rule['mitigations'])
                    try:
                        rule['statement'] = latex_escape_tiny(rule['statement'])
                    except AttributeError:
                        pass
        except KeyError:
            continue
    audit_results = {'audit_results': policy_results}
    latex_jinja_env = jinja2.Environment(
        block_start_string='\\BLOCK{',
        block_end_string='}',
        variable_start_string='\\VAR{',
        variable_end_string='}',
        comment_start_string='\\#{',
        comment_end_string='}',
        line_statement_prefix='%%',
        line_comment_prefix='%#',
        trim_blocks=True,
        autoescape=False,
        loader=jinja2.FileSystemLoader(os.path.abspath('.'))
    )
    template = latex_jinja_env.get_template(template)
    rendered_template = template.render(summary_stats=summary_stats,
                                        failure_stats=failure_stats,
                                        enabled_policy_rules=enabled_policy_rules,
                                        audit_results=audit_results)
    build_dir = ".build"
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    out_file = f"{build_dir}/template"
    with open(out_file, "w") as f:
        f.write(rendered_template)
    try:
        subprocess.run(["cp", "-r", "templates/images", build_dir], check=True)
    except subprocess.CalledProcessError as error:
        logger.error("The copy of templates/images directory into the build directory failed."
                     " Images might not be rendered")
        logger.error(error)
    try:
        logger.info("Running first Latex build of the report.")
        subprocess.run(f"cd {build_dir} && pdflatex -output-directory {os.path.realpath(build_dir)}"
                       f" {os.path.realpath(out_file)}",
                       check=True, shell=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as error:
        logger.error("The first Pdflatex iteration failed.")
        logger.error(error)
    try:
        # build a second time for TOC
        logger.info("Rebuilding report for Table of Contents.")
        subprocess.run(f"cd {build_dir} && pdflatex -output-directory {os.path.realpath(build_dir)}"
                       f" {os.path.realpath(out_file)}",
                       check=True, shell=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as error:
        logger.error("The second Pdflatex iteration failed.")
        logger.error(error)
    copyfile(f"{out_file}.pdf", outfile)
    logger.info(f"Report generated: {outfile}")


def get_summary_stats(policy_results):
    total_tests = len(policy_results)
    successful_tests = len([test for test in policy_results if test['audit-outcome'] == 'pass'])
    failed_tests = total_tests - successful_tests
    success_percentage = round((successful_tests * 100) / total_tests, 2)
    failed_percentage = round((failed_tests * 100) / total_tests, 2)
    compliance_level = "N/A"
    compliance_color = "red"
    if success_percentage < 10:
        compliance_level = "Poor"
        compliance_color = "red!50"
    elif success_percentage < 25:
        compliance_level = "Low"
        compliance_color = "red!30"
    elif success_percentage < 50:
        compliance_level = "Medium"
        compliance_color = "orange!50"
    elif success_percentage < 80:
        compliance_level = "Fair"
        compliance_color = "green!20"
    elif 80 < success_percentage < 100:
        compliance_level = "Good"
        compliance_color = "green!35"
    elif success_percentage == 100:
        compliance_level = "Perfect"
        compliance_color = "green!50"
    summary_stats = {'total_tests': total_tests,
                     'success_tests': successful_tests,
                     'failed_tests': failed_tests,
                     'success_percentage': str(success_percentage),
                     'failed_percentage': str(failed_percentage),
                     'compliance_level': compliance_level,
                     'compliance_color': compliance_color}
    return summary_stats


def get_rules_violation_stats(policy_results, policy):
    total = 0
    violation_stats = dict()
    for rule in policy.get_policy_rules_enabled():
        violation_stats[latex_escape(rule['type'])] = {'count': 0}
    for test in policy_results:
        if test['audit-outcome'] == "fail":
            for failed_test in test['failed-tests']:
                for instance in failed_test:
                    violation_stats[latex_escape(instance['type'])]['count'] += 1
                    total += 1
    if total == 0:
        for key in violation_stats.keys():
            violation_stats[key]['percentage'] = 0
    else:
        for key in violation_stats.keys():
            violation_stats[key]['percentage'] = round(violation_stats[key]['count'] * 100 / total, 2)
    return violation_stats


def latex_escape(string):
    if string is None:
        return "N/A"
    broken_string = '\\allowbreak '.join([string[i:i+25] for i in range(0, len(string), 25)])
    return broken_string.replace('_', "\\_").replace('$', '\\$').replace('%', '\\%').replace('&', '\\&')


def latex_escape_tiny(string):
    if string is None:
        return "N/A"
    broken_string = '\\allowbreak '.join([string[i:i+48] for i in range(0, len(string), 48)])
    return broken_string.replace('_', "\\_").replace('$', '\\$').replace('%', '\\%').replace('&', '\\&')


def main():
    arguments = get_args()
    if arguments.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    policy_file = arguments.policy
    policy = None
    policy_results = list()
    try:
        policy = Policy.DockerfilePolicy(policy_file)
    except FileNotFoundError as error:
        logger.error(error)
        exit(1)
    except TypeError as error:
        logger.error(error)
        exit(1)
    if arguments.dockerfile is not None:
        d = Dockerfile.Dockerfile(arguments.dockerfile)
        policy_result = policy.evaluate_dockerfile(d)
        policy_results.append(policy_result)
    else:
        dockerfiles = os.listdir(arguments.batch)
        dockerfiles = sorted(dockerfiles)
        for file in dockerfiles:
            try:
                d = Dockerfile.Dockerfile(f"{arguments.batch}/{file}")
            except Dockerfile.NotDockerfileError:
                continue
            except Dockerfile.EmptyFileError:
                continue
            policy_result = policy.evaluate_dockerfile(d)
            policy_results.append(policy_result)
    if arguments.json:
        with open("dockerfile-audit.json", "w") as fp:
            json.dump(policy_results, indent=2, sort_keys=True, fp=fp)
    if arguments.report:
        logger.debug("Preparing to generate PDF report.")
        template = arguments.report_template
        outfile = arguments.report_name
        generate_report(policy, policy_results, template, outfile)


if __name__ == '__main__':
    logger = logging.getLogger()
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT)
    main()

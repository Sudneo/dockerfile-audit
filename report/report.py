import jinja2
import logging
import os
import subprocess
from shutil import copyfile

logger = logging.getLogger(__name__)


def generate_latex_report(policy, policy_results, template, outfile):
    logger.info("Starting report generation.")
    failure_stats = __get_rules_violation_stats(policy_results, policy)
    summary_stats = __get_summary_stats(policy_results)
    enabled_policy_rules = {'policy_rules_enabled': policy.get_policy_rules_enabled()}
    for enabled_rule in enabled_policy_rules['policy_rules_enabled']:
        enabled_rule['type'] = __latex_escape(enabled_rule['type'])
        enabled_rule['details'] = __latex_escape(enabled_rule['details'])
    for item in policy_results:
        item['filename'] = __latex_escape(item['filename'])
        try:
            for rule_test in item['failed-tests']:
                for rule in rule_test:
                    rule['type'] = __latex_escape(rule['type'])
                    rule['details'] = __latex_escape(rule['details'])
                    rule['mitigations'] = __latex_escape(rule['mitigations'])
                    try:
                        rule['statement'] = __latex_escape_tiny(rule['statement'])
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


def __get_summary_stats(policy_results):
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


def __get_rules_violation_stats(policy_results, policy):
    total = 0
    violation_stats = dict()
    for rule in policy.get_policy_rules_enabled():
        violation_stats[__latex_escape(rule['type'])] = {'count': 0}
    for test in policy_results:
        if test['audit-outcome'] == "fail":
            for failed_test in test['failed-tests']:
                for instance in failed_test:
                    violation_stats[__latex_escape(instance['type'])]['count'] += 1
                    total += 1
    if total == 0:
        for key in violation_stats.keys():
            violation_stats[key]['percentage'] = 0
    else:
        for key in violation_stats.keys():
            violation_stats[key]['percentage'] = round(violation_stats[key]['count'] * 100 / total, 2)
    return violation_stats


def __latex_escape(string):
    if string is None:
        return "N/A"
    broken_string = '\\allowbreak '.join([string[i:i+25] for i in range(0, len(string), 25)])
    return broken_string.replace('_', "\\_").replace('$', '\\$').replace('%', '\\%').replace('&', '\\&')


def __latex_escape_tiny(string):
    if string is None:
        return "N/A"
    broken_string = '\\allowbreak '.join([string[i:i+48] for i in range(0, len(string), 48)])
    return broken_string.replace('_', "\\_").replace('$', '\\$').replace('%', '\\%').replace('&', '\\&')

import os
import argparse
import logging
import jinja2
from shutil import copyfile
from dockerfile import Dockerfile
from dockerfile import Policy


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--policy", default="policy.yaml", help="The dockerfile policy to use for the audit.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--dockerfile", type=str, help="The Dockerfile to audit.")
    group.add_argument("-b", "--batch", type=str, help="A directory in which all files will be audited.")
    args = parser.parse_args()
    return args


def generate_report(policy, policy_results):
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
    template = latex_jinja_env.get_template('templates/report-template.tex')
    rendered_template = template.render(summary_stats=summary_stats, enabled_policy_rules=enabled_policy_rules,
                                        audit_results=audit_results)
    build_dir = ".build"
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    out_file = f"{build_dir}/template"
    with open(out_file, "w") as f:
        f.write(rendered_template)
    os.system(f"cp -r templates/images {build_dir}")
    os.system(f"cd {build_dir} && pdflatex -output-directory {os.path.realpath(build_dir)} "
              f"{os.path.realpath(out_file)}")
    copyfile(f"{out_file}.pdf", "report.pdf")


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
        for file in dockerfiles:
            try:
                d = Dockerfile.Dockerfile(f"{arguments.batch}/{file}")
            except Dockerfile.NotDockerfileError:
                continue
            except Dockerfile.EmptyFileError:
                continue
            policy_result = policy.evaluate_dockerfile(d)
            policy_results.append(policy_result)
    generate_report(policy, policy_results)


if __name__ == '__main__':
    logger = logging.getLogger()
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT)
    main()

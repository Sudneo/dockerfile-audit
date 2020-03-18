import os
import argparse
import logging
import jinja2
from jinja2 import Template
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


def generate_report(policy_results):
    total_tests = len(policy_results)
    successful_tests = len([test for test in policy_results if test['audit-outcome'] == 'pass'])
    failed_tests = total_tests - successful_tests
    success_percentage = ( successful_tests * 100) / total_tests
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
        loader=jinja2.FileSystemLoader(os.path.abspath('/'))
    )

    pass


def main():
    arguments = get_args()
    policy_file = arguments.policy
    policy = None
    policy_results = list()
    try:
        policy = Policy.DockerfilePolicy(policy_file)
    except FileNotFoundError:
        exit(1)
    except TypeError:
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
    generate_report(policy_results)


if __name__ == '__main__':
    logger = logging.getLogger()
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT)
    main()

import os
import argparse
import logging
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


def main():
    arguments = get_args()
    policy_file = arguments.policy
    policy = None
    try:
        policy = Policy.DockerfilePolicy(policy_file)
    except FileNotFoundError:
        exit(1)
    except TypeError:
        exit(1)
    if arguments.dockerfile is not None:
        d = Dockerfile.Dockerfile(arguments.dockerfile)
        policy_result = policy.evaluate_dockerfile(d)
        print(policy_result)
    else:
        dockerfiles = os.listdir(arguments.batch)
        for file in dockerfiles:
            try:
                d = Dockerfile.Dockerfile(f"{arguments.batch}/{file}")
            except Dockerfile.NotDockerfileError:
                print(f"Failed to parse file {file}. Not a valid Dockerfile.")
                continue
            except Dockerfile.EmptyFileError:
                print(f"File {file} is empty. Skipping.")
                continue
            policy_result = policy.evaluate_dockerfile(d)
            print(policy_result)


if __name__ == '__main__':
    logger = logging.getLogger()
    FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=FORMAT)
    main()
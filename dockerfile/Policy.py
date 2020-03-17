import yaml


class DockerfilePolicy(object):

    def __init__(self, policy_file):
        self.policy_rules = list()
        self.policy_file = policy_file

    
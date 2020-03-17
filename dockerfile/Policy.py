import yaml
from .PolicyRule import *


class DockerfilePolicy(object):

    def __init__(self, policy_file):
        self.policy_rules = list()
        self.policy_file = policy_file
        self.init_rules()

    def evaluate_dockerfile(self, dockerfile_object):
        test_results = list()
        for policy_rule in self.policy_rules:
            test_results.append(policy_rule.test(dockerfile_object.get_directives()))
        return test_results

    def init_rules(self):
        with open(self.policy_file) as file:
            policy_rules = yaml.safe_load(file)
        policies = policy_rules['policy']
        try:
            enforce_registries = policies['enforce_authorized_registries']
            if enforce_registries['enabled']:
                self.policy_rules.append(EnforceRegistryPolicy(enforce_registries['registries']))
        except KeyError:
            logger.debug("No enforce_authorized_registries found in policy, skipping.")






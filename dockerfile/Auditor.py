from dockerfile import Dockerfile


class AuditException(Exception):
    pass


class DockerfileAuditor:

    def __init__(self, policy=None):
        self.policy = policy

    def audit(self, path):
        try:
            dockerfile_object = Dockerfile.Dockerfile(path)
        except (Dockerfile.NotDockerfileError, Dockerfile.EmptyFileError):
            raise AuditException(f"Could not perform audit on {path}.")
        policy_result = self.policy.evaluate_dockerfile(dockerfile_object)
        return policy_result

    @staticmethod
    def parse_only(path):
        try:
            dockerfile_object = Dockerfile.Dockerfile(path)
        except (Dockerfile.NotDockerfileError, Dockerfile.EmptyFileError):
            raise AuditException(f"Could not process {path}.")
        result = {'filename': dockerfile_object.get_filename(),
                  'path': dockerfile_object.get_path(),
                  'maintainers': dockerfile_object.get_maintainers(),
                  'directives': dockerfile_object.get_directives()}
        return result

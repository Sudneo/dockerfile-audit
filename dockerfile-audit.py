import os
from dockerfile import Dockerfile

dockerfiles = os.listdir('dockerfiles')
for file in dockerfiles:
    d = Dockerfile.Dockerfile(f"/home/daniele/dev/dockerfile-audit/dockerfiles/{file}")
    print(d.get_directives())

FROM funkyfuture/nest-of-serpents

ENTRYPOINT tox
WORKDIR /src

RUN pyp install tox flake8
ADD . .

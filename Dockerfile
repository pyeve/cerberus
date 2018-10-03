FROM funkyfuture/nest-of-serpents

ENTRYPOINT tox
WORKDIR /src

RUN pip3.7 install black flake8 pre-commit pytest tox PyYAML Sphinx \
 && mkdir /home/tox \
 && mv /root/.cache /home/tox/

RUN useradd -m tox \
 && chown -R tox.tox /home/tox/.cache

ADD . .
RUN mkdir .tox \
 && chown -R tox.tox .

USER tox

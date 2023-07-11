FROM fedora:35

ENTRYPOINT tox
WORKDIR /src

RUN dnf -y install python3-devel python3-pip

RUN pip3 install black flake8 pre-commit pytest tox PyYAML Sphinx \
 && mkdir /home/tox \
 && mv /root/.cache /home/tox/

RUN useradd -m tox \
 && chown -R tox.tox /home/tox/.cache

ADD . .
RUN mkdir .tox \
 && chown -R tox.tox .

USER tox

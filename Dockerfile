FROM funkyfuture/nest-of-serpents

ENTRYPOINT tox
WORKDIR /src

RUN pip3.6 install flake8 pytest tox PyYAML Sphinx==1.5.6 \
 && mkdir /home/tox \
 && mv /root/.cache /home/tox/

RUN useradd -m tox \
 && chown -R tox.tox /home/tox/.cache

ADD . .
RUN mkdir .tox \
 && chown -R tox.tox .

USER tox

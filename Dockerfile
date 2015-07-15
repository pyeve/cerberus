FROM funkyfuture/nest-of-serpents

ENTRYPOINT tox
WORKDIR /src

RUN apt-get -q update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -qy \
        make \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && pyp install flake8 pytest tox PyYAML Sphinx \
 && mkdir /home/tox \
 && mv /root/.cache /home/tox/

# this will be set to the user's id who's running a script that uses this
# image in order to have file-ownerships on the host-system
# at some point there should be native Docker-implementation for this
ENV TOX_USER_ID=1000
RUN useradd --uid=$TOX_USER_ID -m tox \
 && chown -R tox.tox /home/tox/.cache

ADD . .
RUN chown -R tox.tox .

USER tox

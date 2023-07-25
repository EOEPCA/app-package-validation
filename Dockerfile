FROM python:3.7
RUN pip3 install \
    jhsingle-native-proxy>=0.0.9 \
    streamlit \
    streamlit_code_editor \
    cwltool \
    pyyaml \
    loguru \
    requests

# create a user, since we don't want to run as root
RUN useradd -m jovyan
ENV HOME=/home/jovyan
WORKDIR $HOME


COPY --chown=jovyan:jovyan . /workspaces/app-package-validator
RUN cd /workspaces/app-package-validator && python3 setup.py install

COPY --chown=jovyan:jovyan entrypoint.sh /home/jovyan
RUN chmod +x /workspaces/app-package-validator/entrypoint.sh
USER jovyan

EXPOSE 8888

ENTRYPOINT ["/workspaces/app-package-validator/entrypoint.sh"]

CMD ["jhsingle-native-proxy", "--destport", "8505", "streamlit", "run" "/workspaces/app-package-validator/demo/app.py", "{--}server.port", "{port}", "{--}server.headless", "True", "{--}server.enableCORS", "False", "--port", "8888"]
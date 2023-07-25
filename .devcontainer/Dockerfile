FROM mambaorg/micromamba

USER root

ENV USERNAME=mambauser

ENV PATH=/opt/conda/envs/env_mamba/bin:$PATH

RUN apt-get update -y \
 && apt-get upgrade -y \
 && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl sudo git nodejs wget curl git-flow

RUN echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

RUN chown -R mambauser:1000 /opt/conda/

USER mambauser

ADD .devcontainer/environment.yml /tmp/environment.yml

RUN micromamba create -f /tmp/environment.yml

ENV PATH=/opt/conda/envs/env_mamba/bin:$PATH \
    CONDA_DEFAULT_ENV=env_mamba \
    ENV_NAME=env_mamba \
    CONDA_PROMPT_MODIFIER=(env_mamba)
#ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/:/opt/conda/envs/env_mamba/lib/

WORKDIR /home/mambauser

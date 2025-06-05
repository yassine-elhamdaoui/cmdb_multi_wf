ARG set_proxy=false
FROM container-registry.oracle.com/os/oraclelinux:9-slim-fips AS base
SHELL [ "/bin/bash", "-x", "-e", "-o", "pipefail", "-c" ]

ARG APP_NAME=python
LABEL maintainer="ACS-GENESIS-TIER3_WW@ORACLE.COM"

ENV PORT 8000
ENV HOST "0.0.0.0"
ENV https_proxy="http://www-proxy-hqdc.us.oracle.com:80"
ENV no_proxy="localhost,127.0.0.1,.us.oracle.com,.oraclecorp.com,oraclecloud.com,oraclevcn.com"


RUN microdnf update -y && microdnf install -y oraclelinux-developer-release-el9 python3.12 python3.12-pip && microdnf clean all
RUN  microdnf -y install zip findutils
RUN  microdnf clean all

RUN useradd -ms /bin/bash --uid 1001 $APP_NAME

WORKDIR /opt/app
COPY --chown=$APP_NAME app ./app
COPY --chown=$APP_NAME requirements.txt ./requirements.txt
COPY --chown=$APP_NAME wait_for_sidecar.sh ./wait_for_sidecar.sh
RUN chown $APP_NAME.$APP_NAME -R .
RUN chmod +x ./wait_for_sidecar.sh

USER $APP_NAME

ENV PYTHONPATH "/opt/app"
ENV PATH="/home/python/.local/bin:$PATH"
ENV PATH="/opt/app:$PATH"


RUN python3.12 -m pip install --no-cache-dir --user --upgrade pip
RUN python3.12 -m pip install --no-cache-dir --user --upgrade -r requirements.txt

RUN echo "PYTHONPATH: $PYTHONPATH"
RUN echo "PATH: $PATH"
RUN echo "/home/python/.local/bin:" && ls -la /home/python/.local/bin
RUN echo "WORKDIR:" && ls -Rla $WORKDIR
#RUN echo "which python:" && which python3.12
RUN echo "python version:" && python3.12 --version

EXPOSE 8080

FROM base AS proxy-true
ENV http_proxy="mesh-proxy.istio-system.svc.cluster.local:80"
ENV https_proxy="mesh-proxy.istio-system.svc.cluster.local:80"
ENV no_proxy="localhost,127.0.0.1,.svc.cluster.local,.opc.oracleoutsourcing.com,.us.oracle.com,.oraclecorp.com,oraclecloud.com,.oraclevcn.com,oraclevcn.com"

FROM base AS proxy-false
ENV https_proxy=""
ENV no_proxy=""

FROM proxy-${set_proxy} AS final

CMD ["python3.12", "app/main.py"]


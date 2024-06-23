FROM python:3.10-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY lnkdnlm ./lnkdnlm
ENV PYTHONPATH=/usr/src/app

RUN useradd -M -s /bin/bash lnkdnlm && chown -R lnkdnlm:lnkdnlm /usr/src/app
USER lnkdnlm

CMD [ "python", "lnkdnlm/main.py" ]

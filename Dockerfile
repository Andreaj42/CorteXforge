FROM ghcr.io/cortexlab/cxlb-gnuradio-3.10:1.5

COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir sigmf==1.2.12

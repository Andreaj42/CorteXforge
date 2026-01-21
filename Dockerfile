FROM ghcr.io/cortexlab/cxlb-gnuradio-3.10:1.5

COPY requirements-cortexlab.txt .

RUN pip install --no-cache-dir -r requirements-cortexlab.txt

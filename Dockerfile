FROM ubuntu:22.04

ENV ECCODES_VERSION=2.35.0
ENV ECCODES_URL=https://confluence.ecmwf.int/download/attachments/45757960/eccodes-2.35.0-Source.tar.gz?api=v2
ENV AEC_VERSION=1.1.3
ENV ICON_CACHE_DIR=/tmp/icon_cache

WORKDIR /code

COPY dwdGribExtractor /code/dwdGribExtractor/dwdGribExtractor/
COPY setup.py /code/dwdGribExtractor/
COPY README.rst /code/dwdGribExtractor/
COPY app /code/app

RUN apt update && apt upgrade -y 

RUN apt install -y build-essential gfortran cmake curl

# install libaec (compression library for grib files)
RUN curl -L https://github.com/MathisRosenhauer/libaec/releases/download/v${AEC_VERSION}/libaec-${AEC_VERSION}.tar.gz | tar xz \
    && cd libaec-${AEC_VERSION}  \
    && mkdir build && cd build \
    && ../configure \
    && make check install \
    && cd /code && rm -rf libaec-${AEC_VERSION}

#install eccodes (library for IO of grib files)
RUN cd /code && curl ${ECCODES_URL} | tar xz \
    && mkdir eccodes-build && cd eccodes-build \
    && cmake ../eccodes-${ECCODES_VERSION}-Source \
    && make && ctest \
    && make install \
    && cd /code && rm -rf eccodes-*

RUN apt install -y python3.11 python3-pip python3.11-dev

RUN python3.11 -m pip install --upgrade pip \
    && python3.11 -m pip install /code/dwdGribExtractor

RUN python3.11 -m pip install -r /code/app/requirements.txt

# some cleanup
RUN apt remove -y build-essential gfortran cmake curl \
    && apt autoremove -y \
    && apt clean

EXPOSE 80

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "80"]



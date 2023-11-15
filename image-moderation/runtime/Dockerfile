FROM public.ecr.aws/lambda/python:3.9

COPY . ${LAMBDA_TASK_ROOT}
RUN chmod +xxx ${LAMBDA_TASK_ROOT}/app.py

# dev tools to build zbar
RUN mkdir -p /build/lib
RUN yum groupinstall -y "Development Tools"
RUN mkdir /root/zbar
RUN git clone https://github.com/mchehab/zbar.git /root/zbar
WORKDIR /root/zbar
RUN autoreconf -vfi -I /root/zbar
RUN ./configure --prefix=/usr --without-xshm --without-xv --without-jpeg --without-imagemagick --without-gtk --without-python --without-qt --disable-video
RUN make
RUN mkdir -p /build/lib
RUN cp -a zbar/.libs/libzbar.so* /build/lib

# configure up zbar
RUN echo $LD_LIBRARY_PATH
ENV LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/build/lib"
RUN echo $LD_LIBRARY_PATH

WORKDIR /

COPY requirements.txt .
RUN pip3 install -r requirements.txt -t "${LAMBDA_TASK_ROOT}"

RUN yum install shadow-utils -y
RUN /usr/sbin/useradd -ms /bin/bash app

USER app
CMD /bin/bash

WORKDIR /
CMD ["app.app"]
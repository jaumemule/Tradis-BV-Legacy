FROM python:3.6

RUN mkdir /usr/app

RUN apt-get update \
&& apt-get install -y rsyslog \
&& ln -sf /dev/stdout /var/log/syslog

RUN pip3 install pipenv \
&& pip3 install requests \
&& pip3 install numpy \
&& pip3 install cython \
&& pip3 install pandas \
&& pip3 install schedule \
&& pip3 install apscheduler \
&& pip3 install slackclient \
&& pip3 install pymongo \
&& pip3 install mem_top \
&& pip3 install psutil

RUN pip3 install keras \
&& pip3 install sklearn \
&& pip3 install tensorflow

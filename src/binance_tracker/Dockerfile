FROM python:3.6

RUN mkdir /usr/app
WORKDIR /usr/app/src/binance_tracker

RUN apt-get update
RUN apt-get -y install curl
RUN apt-get -y install ntpdate

RUN pip3 install python-binance==0.7.1
RUN pip3 install dateparser
RUN pip3 install pandas
RUN pip3 install pymongo
RUN pip3 install slackclient==1.3.1

ADD . .

ENTRYPOINT ["/bin/bash", "bin/build"]

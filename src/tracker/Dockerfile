FROM python:3.6 
 
RUN mkdir /usr/app 
WORKDIR /usr/app/src/tracker

RUN apt-get update
RUN apt-get -y install curl
RUN apt-get -y install ntpdate

RUN pip3 install rq==1.1.0
RUN pip3 install python-binance==0.7.1
RUN pip3 install dateparser
RUN pip3 install pipenv
RUN pip3 install requests 
RUN pip3 install numpy 
RUN pip3 install cython 
RUN pip3 install pandas 
RUN pip3 install schedule 
RUN pip3 install apscheduler 
RUN pip3 install slackclient==1.3.1
RUN pip3 install pymongo 
RUN pip3 install ccxt==1.26.45
RUN pip3 install pyOpenSSL==19.1.0
RUN pip3 install pymongo[srv]

ADD . .
 
ENTRYPOINT ["/bin/bash", "bin/build"] 

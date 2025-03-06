FROM python:3.6

RUN mkdir /usr/app
WORKDIR /usr/app/src/director

RUN apt-get update
RUN apt-get install -y awscli

RUN pip install --upgrade pip

RUN pwd
RUN pip3 install supervisor==4.2.1
RUN pip3 install rq==1.1.0
RUN pip3 install certifi==2019.3.9
RUN pip3 install future==0.17.1
RUN pip3 install gast==0.2.2
RUN pip3 install gdax==1.0.6
RUN pip3 install gym==0.12.1
RUN pip3 install h5py==2.9.0
RUN pip3 install more-itertools==4.2.0
RUN pip3 install networkx==2.2
RUN pip3 install numpy==1.16.2
RUN pip3 install pandas==0.24.2
RUN pip3 install protobuf==3.6.1
RUN pip3 install psycopg2==2.7.3
RUN pip3 install py==1.5.4
RUN pip3 install requests==2.13.0
RUN pip3 install ruamel.yaml==0.15.89
RUN pip3 install scikit-learn==0.19.1
RUN pip3 install scipy==1.2.1
RUN pip3 install sklearn==0.0
RUN pip3 install slackclient==1.3.0
RUN pip3 install SQLAlchemy==1.4.2
RUN pip3 install tensorboard==1.13.1
RUN pip3 install tensorflow-estimator==1.13.0
RUN pip3 install tensorflow==1.13.1
RUN pip3 install tensorflow-tensorboard==1.5.1
RUN pip3 install tqdm==4.31.1
RUN pip3 install websocket-client==0.40.0
RUN pip3 install pymongo==3.10.1
RUN pip3 install schedule
RUN pip3 install apscheduler
RUN pip3 install python-box==3.1.1
RUN pip3 install gym==0.13.1
RUN pip3 install Keras==2.2.4
RUN pip3 install keras-rl==0.4.2
RUN pip3 install stable-baselines==2.8.0
RUN pip3 install optuna==2.5.0
RUN pip3 install pymongo[srv]

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
 tar -xzf ta-lib-0.4.0-src.tar.gz && \
 (cd ta-lib && ./configure --prefix=/usr) && \
 (cd ta-lib && make) && \
 (cd ta-lib && make install)

RUN pip3 install ta-lib

ADD . .

ENTRYPOINT ["/bin/bash", "bin/supervisord_start.sh"]

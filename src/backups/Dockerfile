FROM mongo

RUN mkdir backups
WORKDIR backups

RUN apt-get update
RUN apt-get -y install curl
RUN apt-get -y install ntpdate

ENTRYPOINT ["/bin/bash", "bin/backupS3"]

ADD . .

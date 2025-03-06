FROM golang

ADD . .
WORKDIR ./src/director

RUN go get .
RUN go build

CMD go get github.com/pilu/fresh && \
	fresh main.go; \
	fi
	
EXPOSE 3003

FROM node:carbon

WORKDIR /usr/app
COPY . .
RUN npm install --only=production \
 && npm install -g nodemon

EXPOSE 3000
CMD [ "npm", "start" ]

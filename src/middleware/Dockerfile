FROM node:carbon

WORKDIR /usr/app
COPY . .
RUN npm install --only=production \
 && npm install -g nodemon

EXPOSE 3001
CMD [ "npm", "start" ]

FROM node:carbon

WORKDIR /usr/app
COPY . .
RUN npm install --only=production
RUN PORT=3001 npm run build

CMD npm run start:prod

FROM node:14

RUN npm install --global smee-client

CMD [ "smee", "-u", "https://smee.io/q0qaHUsXP1FmiKt2", "--target", "http://172.17.0.2:8080/github-webhook/" ]

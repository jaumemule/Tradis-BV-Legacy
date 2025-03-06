# Middleware

1. RUN IT: go to the root directory of the middleware and run into `./src/bin/debug_server`. This will deploy the API by running a daemon `nodemon` and install its dependencies using `npm`. You need to have installed `npm`  (on Mac you can use Brew for that), `nodemon` and `NodeJS` globally. The exposed port will be `8070` and the whole hostname + port + prefix should be `http://localhost:8070/api/v1` (use postman for requesting). Sadly, the project does not support Docker development yet for it yet, so:
	1. `npm`: dependency manager. Orquestrates all the NodeJS dependencies installed on the wallet, but you can also use it for your global dependencies such as `nodemon`
	2. `nodemon`: daemon for running NodeJS locally. It watches to the project changes and reflects them in live. Essential for local development `npm install -g nodemon` (while `-g` installs globally in your computer).
	3. `NodeJS`: yeah, well, latest ECMAScript language version (please update after installing!)

While running:

- Set headers `client-id` and `client-secret` to access to the middleware services (just a layer of security). Not set or wrong will drop `HTTP 401`
- Health endpoint will always return `HTTP 200`
- Login endpoint will return `HTTP 200` or `HTTP 400`

Postman collection: https://www.getpostman.com/collections/5922d3fcdc609dbefdc4

## Authentication

Use `POST /api/v1/login` with `username` and `password` parameters to authenticate and obtain a JWT token.

Use this JWT token in `Authorization: Bearer` header for all other requests.

Registering new users is currently not supported in the business logic. The authentication relies on a _static_ SQLite database with a set of username/password pairs. When authentication is required, it's advised to migrate from SQLite to a MySQL server.

### users.db

```SQLite
CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password TEXT);

INSERT INTO users (username, password) VALUES ('admin', 'd033e22ae348aeb5660fc2140aec35850c4da997'); // password=admin
```
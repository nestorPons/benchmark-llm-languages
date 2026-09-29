"use strict";
#;
#;
API;
Endpoints
    - `POST /auth/login`;
Authenticate;
and;
receive;
a;
JWT;
token.
    - `GET /health`;
Check;
server;
health(no, authentication, required).
    - `POST /items`;
Create;
a;
new item(requires, authentication).
    - `GET /items`;
Retrieve;
all;
items(requires, authentication).
    - `GET /items/{id}`;
Retrieve;
a;
specific;
item;
by;
ID(requires, authentication).
    - `PUT /items/{id}`;
Update;
a;
specific;
item;
by;
ID(requires, authentication).
    - `DELETE /items/{id}`;
Delete;
a;
specific;
item;
by;
ID(requires, authentication).
;
#;
#;
Authentication;
Use;
the;
following;
credentials;
to;
authenticate: -Username;
`admin`
    - Password;
`secret`;

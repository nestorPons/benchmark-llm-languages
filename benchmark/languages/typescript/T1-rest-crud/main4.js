"use strict";
// app/prisma/schema.prisma
generator;
client;
{
    provider = "prisma-client-js";
}
datasource;
db;
{
    provider = "sqlite";
    url = "file:./dev.db";
}
model;
Item;
{
    id;
    Int;
    (autoincrement());
    name;
    String;
    description;
    String ?
        price : ;
    Float;
    created_at;
    DateTime;
    (now());
}

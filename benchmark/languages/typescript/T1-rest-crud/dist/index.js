"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fastify_1 = __importDefault(require("fastify"));
const jwt_1 = __importDefault(require("@fastify/jwt"));
const better_sqlite3_1 = __importDefault(require("better-sqlite3"));
const items_1 = require("./routes/items");
const auth_1 = require("./routes/auth");
const server = (0, fastify_1.default)();
const db = new better_sqlite3_1.default('./data/database.sqlite');
server.decorate('db', db);
server.register(jwt_1.default, {
    secret: 'supersecret'
});
server.get('/health', async (request, reply) => {
    return { status: 'ok' };
});
server.register(auth_1.authRoutes);
server.register(items_1.itemRoutes);
const start = async () => {
    try {
        await server.listen({ port: 8005 });
        console.log('Server listening on http://localhost:8005');
    }
    catch (err) {
        server.log.error(err);
        process.exit(1);
    }
};
start();

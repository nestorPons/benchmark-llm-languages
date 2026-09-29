"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.authRoutes = authRoutes;
async function authRoutes(server) {
    server.post('/auth/login', async (request, reply) => {
        const { username, password } = request.body;
        if (username === 'admin' && password === 'secret') {
            const token = server.jwt.sign({ username });
            return reply.send({ token });
        }
        return reply.status(401).send({ error: 'Unauthorized' });
    });
}

import { FastifyInstance } from 'fastify';

export async function authRoutes(server: FastifyInstance) {
  server.post('/auth/login', async (request, reply) => {
    const { username, password } = request.body as { username: string; password: string };

    if (username === 'admin' && password === 'secret') {
      const token = server.jwt.sign({ username });
      return reply.send({ token });
    }

    return reply.status(401).send({ error: 'Unauthorized' });
  });
}
import Fastify from 'fastify';
import fastifyJwt from '@fastify/jwt';
import Database from 'better-sqlite3';
import { itemRoutes } from './routes/items';
import { authRoutes } from './routes/auth';

declare module 'fastify' {
  interface FastifyInstance {
    db: Database.Database;
  }
}

const server = Fastify();
const db = new Database('./data/database.sqlite');

server.decorate('db', db);

server.register(fastifyJwt, {
  secret: 'supersecret'
});

server.get('/health', async (request, reply) => {
  return { status: 'ok' };
});

server.register(authRoutes);
server.register(itemRoutes);

const start = async () => {
  try {
    await server.listen({ port: 8005 });
    console.log('Server listening on http://localhost:8005');
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
};

start();
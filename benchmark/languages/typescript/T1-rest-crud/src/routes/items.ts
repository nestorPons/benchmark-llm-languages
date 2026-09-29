import { FastifyInstance } from 'fastify';

export async function itemRoutes(server: FastifyInstance) {
  server.addHook('onRequest', async (request, reply) => {
    try {
      await request.jwtVerify();
    } catch (err) {
      return reply.send(err);
    }
  });

  server.post('/items', async (request, reply) => {
    const { name, description, price } = request.body as { name: string; description: string; price: number };

    if (price < 0) {
      return reply.status(400).send({ error: 'Price must be non-negative' });
    }

    const stmt = server.db.prepare(
      'INSERT INTO items (name, description, price, created_at) VALUES (?, ?, ?, ?)'
    );
    const info = stmt.run(name, description, price, new Date().toISOString());

    return reply.status(201).send({ id: info.lastInsertRowid });
  });

  server.get('/items', async (request, reply) => {
    const stmt = server.db.prepare('SELECT * FROM items');
    const items = stmt.all();
    return reply.send(items);
  });

  server.get('/items/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const stmt = server.db.prepare('SELECT * FROM items WHERE id = ?');
    const item = stmt.get(id);

    if (!item) {
      return reply.status(404).send({ error: 'Item not found' });
    }

    return reply.send(item);
  });

  server.put('/items/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const { name, description, price } = request.body as { name: string; description: string; price: number };

    if (price < 0) {
      return reply.status(400).send({ error: 'Price must be non-negative' });
    }

    const stmt = server.db.prepare(
      'UPDATE items SET name = ?, description = ?, price = ? WHERE id = ?'
    );
    const info = stmt.run(name, description, price, id);

    if (info.changes === 0) {
      return reply.status(404).send({ error: 'Item not found' });
    }

    return reply.send({ id });
  });

  server.delete('/items/:id', async (request, reply) => {
    const { id } = request.params as { id: string };
    const stmt = server.db.prepare('DELETE FROM items WHERE id = ?');
    const info = stmt.run(id);

    if (info.changes === 0) {
      return reply.status(404).send({ error: 'Item not found' });
    }

    return reply.status(204).send();
  });
}
// app/src/routes/items.ts
import { FastifyInstance } from 'fastify';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export async function itemRoutes(fastify: FastifyInstance) {
  fastify.post('/', { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const { name, description, price } = request.body as { name: string; description: string; price: number };

    if (price < 0) {
      return reply.status(400).send({ error: 'Price must be non-negative' });
    }

    const item = await prisma.item.create({
      data: { name, description, price, created_at: new Date() }
    });

    reply.status(201).send(item);
  });

  fastify.get('/', { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const items = await prisma.item.findMany();
    reply.send(items);
  });

  fastify.get('/:id', { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const { id } = request.params as { id: string };
    const item = await prisma.item.findUnique({ where: { id: Number(id) } });

    if (!item) {
      return reply.status(404).send({ error: 'Item not found' });
    }

    reply.send(item);
  });

  fastify.put('/:id', { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const { id } = request.params as { id: string };
    const { name, description, price } = request.body as { name: string; description: string; price: number };

    if (price < 0) {
      return reply.status(400).send({ error: 'Price must be non-negative' });
    }

    const item = await prisma.item.update({
      where: { id: Number(id) },
      data: { name, description, price }
    });

    reply.send(item);
  });

  fastify.delete('/:id', { preHandler: [fastify.authenticate] }, async (request, reply) => {
    const { id } = request.params as { id: string };

    await prisma.item.delete({ where: { id: Number(id) } });

    reply.status(204).send();
  });
}
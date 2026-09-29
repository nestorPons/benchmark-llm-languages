"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.itemRoutes = itemRoutes;
const client_1 = require("@prisma/client");
const prisma = new client_1.PrismaClient();
async function itemRoutes(fastify) {
    fastify.post('/', { preHandler: [fastify.authenticate] }, async (request, reply) => {
        const { name, description, price } = request.body;
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
        const { id } = request.params;
        const item = await prisma.item.findUnique({ where: { id: Number(id) } });
        if (!item) {
            return reply.status(404).send({ error: 'Item not found' });
        }
        reply.send(item);
    });
    fastify.put('/:id', { preHandler: [fastify.authenticate] }, async (request, reply) => {
        const { id } = request.params;
        const { name, description, price } = request.body;
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
        const { id } = request.params;
        await prisma.item.delete({ where: { id: Number(id) } });
        reply.status(204).send();
    });
}

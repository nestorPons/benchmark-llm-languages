import Fastify, { FastifyRequest } from 'fastify';
import Database from 'better-sqlite3';
import jwt from 'jsonwebtoken';
import { createHash, readFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';

const SECRET = 'benchmark-secret';
const DB_FILE = 'test.db';

if (!existsSync(DB_FILE)) {
  execSync(`sqlite3 ${DB_FILE} < data/schema.sql`);
}
const db = new Database(DB_FILE);
const adminHash = createHash('sha256').update('secret').digest('hex');
db.prepare('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)').run('admin', adminHash);

const app = Fastify();

function auth(request: FastifyRequest): string {
  const header = request.headers.authorization || '';
  const token = header.replace(/^Bearer\s+/i, '');
  try {
    const payload = jwt.verify(token, SECRET) as { sub: string };
    return payload.sub;
  } catch {
    throw Object.assign(new Error('Invalid token'), { statusCode: 401 });
  }
}

app.get('/health', async () => ({ ok: true }));

app.post('/auth/login', async (request) => {
  const { username, password } = request.body as { username: string; password: string };
  const row = db.prepare('SELECT * FROM users WHERE username = ?').get(username) as any;
  const h = createHash('sha256').update(password || '').digest('hex');
  if (!row || row.password !== h) {
    throw Object.assign(new Error('Incorrect username or password'), { statusCode: 401 });
  }
  return { token: jwt.sign({ sub: username }, SECRET, { expiresIn: '1h' }) };
});

app.post('/items', async (request) => {
  auth(request);
  const { name, description, price } = request.body as any;
  if (price < 0) throw Object.assign(new Error('price must be >= 0'), { statusCode: 400 });
  const info = db.prepare('INSERT INTO items (name, description, price) VALUES (?,?,?)').run(name, description ?? null, price);
  return db.prepare('SELECT * FROM items WHERE id = ?').get(info.lastInsertRowid);
});

app.get('/items', async (request) => {
  auth(request);
  return db.prepare('SELECT * FROM items').all();
});

app.get('/items/:id', async (request) => {
  auth(request);
  const row = db.prepare('SELECT * FROM items WHERE id = ?').get((request.params as any).id);
  if (!row) throw Object.assign(new Error('not found'), { statusCode: 404 });
  return row;
});

app.put('/items/:id', async (request) => {
  auth(request);
  const { name, description, price } = request.body as any;
  if (price < 0) throw Object.assign(new Error('price must be >= 0'), { statusCode: 400 });
  const info = db.prepare('UPDATE items SET name=?, description=?, price=? WHERE id=?')
    .run(name, description ?? null, price, (request.params as any).id);
  if (info.changes === 0) throw Object.assign(new Error('not found'), { statusCode: 404 });
  return { id: Number((request.params as any).id), name, description, price };
});

app.delete('/items/:id', async (request, reply) => {
  auth(request);
  const info = db.prepare('DELETE FROM items WHERE id=?').run((request.params as any).id);
  if (info.changes === 0) throw Object.assign(new Error('not found'), { statusCode: 404 });
  reply.code(204).send();
});

app.listen({ host: '0.0.0.0', port: 8005 });

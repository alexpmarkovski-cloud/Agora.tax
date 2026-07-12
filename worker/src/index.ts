import { Hono } from 'hono';
import type { Env } from './env';
import { landingRoute } from './routes/landing';
import { legalRoute } from './routes/legal';

const app = new Hono<{ Bindings: Env }>();

app.route('/', landingRoute);
app.route('/legal', legalRoute);

export default app;

/**
 * Sample Express.js Application for testing API Documentation Agent.
 * Demonstrates express.Router(), app.use() prefixes, middleware chains, route parameters, and JSDoc comments.
 */

const express = require('express');
const app = express();
const router = express.Router();

app.use(express.json());

// Dummy Auth Middleware
function authMiddleware(req, res, next) {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).json({ error: 'Token missing' });
  next();
}

/**
 * Health check endpoint for monitoring system status.
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime() });
});

/**
 * Get paginated list of tasks.
 * Supports limit and status filters.
 */
router.get('/tasks', (req, res) => {
  res.json([
    { id: 't-101', title: 'Complete API Agent', status: 'in_progress' }
  ]);
});

/**
 * Create a new task item.
 * Requires authMiddleware token.
 */
router.post('/tasks', authMiddleware, (req, res) => {
  const { title, description } = req.body;
  res.status(201).json({
    id: 't-102',
    title,
    description,
    createdAt: new Date().toISOString()
  });
});

/**
 * Fetch detailed task info by unique string ID.
 */
router.get('/tasks/:id', (req, res) => {
  const { id } = req.params;
  res.json({ id, title: 'Sample Task', status: 'completed' });
});

/**
 * Update task status or details by ID.
 * Requires authMiddleware token.
 */
router.put('/tasks/:id', authMiddleware, (req, res) => {
  const { id } = req.params;
  res.json({ id, updated: true });
});

/**
 * Delete task entry from database by ID.
 * Requires authMiddleware token.
 */
router.delete('/tasks/:id', authMiddleware, (req, res) => {
  res.json({ success: true, message: `Task ${req.params.id} deleted` });
});

// Mount router under /api/v1 prefix
app.use('/api/v1', router);

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Express server running on port ${PORT}`);
});

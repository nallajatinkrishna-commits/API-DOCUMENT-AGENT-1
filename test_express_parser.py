import pytest
from backend.parsers.express_parser import ExpressParser


def test_express_parser_can_parse():
    parser = ExpressParser()
    assert parser.can_parse("server.js", "const express = require('express');") is True
    assert parser.can_parse("app.ts", "import express from 'express';") is True
    assert parser.can_parse("main.py", "import os") is False


def test_express_endpoint_extraction():
    code = """
const express = require('express');
const app = express();
const router = express.Router();

function authMiddleware(req, res, next) { next(); }

/**
 * Get server status.
 */
app.get('/status', (req, res) => {
    res.json({ ok: true });
});

/**
 * Fetch task details by ID.
 */
router.get('/tasks/:id', (req, res) => {
    res.json({ id: req.params.id });
});

/**
 * Create a new task.
 */
router.post('/tasks', authMiddleware, (req, res) => {
    res.status(201).json(req.body);
});

app.use('/api/v1', router);
"""
    parser = ExpressParser()
    endpoints = parser.parse("server.js", code)

    assert len(endpoints) >= 3

    status_ep = next((ep for ep in endpoints if ep.path == "/status"), None)
    assert status_ep is not None
    assert status_ep.method == "GET"

    task_ep = next((ep for ep in endpoints if "/tasks/{id}" in ep.path or "/tasks/:id" in ep.path), None)
    assert task_ep is not None
    assert task_ep.method == "GET"
    assert len(task_ep.parameters) > 0

    post_ep = next((ep for ep in endpoints if ep.method == "POST" and "tasks" in ep.path), None)
    assert post_ep is not None
    assert "authMiddleware" in post_ep.auth_middleware

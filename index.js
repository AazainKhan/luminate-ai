// index.js
const express = require("express");
const axios = require("axios");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
require("dotenv").config();

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;
const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const BASE_URL = process.env.BASE_URL; // e.g. https://luminate-ai-backend.onrender.com
const BB_HOST = process.env.BB_HOST || "https://luminate.centennialcollege.ca";
const TOKENS_FILE = path.join(__dirname, "tokens.json");

if (!CLIENT_ID || !CLIENT_SECRET || !BASE_URL) {
    console.error("Missing required env vars: CLIENT_ID, CLIENT_SECRET, BASE_URL");
    process.exit(1);
}

// simple token storage (file). Not production-grade.
function loadAllTokens() {
    try {
        return JSON.parse(fs.readFileSync(TOKENS_FILE, "utf8") || "{}");
    } catch {
        return {};
    }
}
function saveAllTokens(obj) {
    fs.writeFileSync(TOKENS_FILE, JSON.stringify(obj, null, 2));
}
function saveTokensFor(userId, tokenObj) {
    const all = loadAllTokens();
    all[userId] = tokenObj;
    saveAllTokens(all);
}
function getTokensFor(userId) {
    const all = loadAllTokens();
    return all[userId];
}
function removeTokensFor(userId) {
    const all = loadAllTokens();
    delete all[userId];
    saveAllTokens(all);
}

// state store for CSRF protection (in-memory, fine for dev)
const states = new Set();

// helper: create token object from token response
function tokenFromResponse(data) {
    const expiresIn = parseInt(data.expires_in || 3600, 10);
    return {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        expires_at: Date.now() + expiresIn * 1000 - 60000 // 1 min buffer
    };
}

// refresh flow
async function refreshIfNeeded(userId) {
    const tokens = getTokensFor(userId);
    if (!tokens) throw new Error("no tokens for user");
    if (Date.now() < (tokens.expires_at || 0)) return tokens.access_token;

    // refresh
    const params = new URLSearchParams({
        grant_type: "refresh_token",
        refresh_token: tokens.refresh_token,
        redirect_uri: `${BASE_URL}/auth/callback`
    });

    const basic = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64");
    const resp = await axios.post(`${BB_HOST}/learn/api/public/v1/oauth2/token`, params.toString(), {
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            Authorization: `Basic ${basic}`
        }
    });

    const newTokens = tokenFromResponse(resp.data);
    saveTokensFor(userId, newTokens);
    return newTokens.access_token;
}

// Step 1: start auth
app.get("/auth/start", (req, res) => {
    const state = crypto.randomBytes(16).toString("hex");
    states.add(state);
    const redirectUri = encodeURIComponent(`${BASE_URL}/auth/callback`);
    const url = `${BB_HOST}/learn/api/public/v1/oauth2/authorizationcode?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${redirectUri}&state=${state}`;
    res.redirect(url);
});

// Step 2: callback
app.get("/auth/callback", async (req, res) => {
    try {
        const { code, state } = req.query;
        if (!code) return res.status(400).send("missing code");
        if (!state || !states.has(state)) return res.status(400).send("invalid state");
        states.delete(state);

        const params = new URLSearchParams({
            grant_type: "authorization_code",
            code,
            redirect_uri: `${BASE_URL}/auth/callback`
        });

        const basic = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64");
        const tokenResp = await axios.post(`${BB_HOST}/learn/api/public/v1/oauth2/token`, params.toString(), {
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                Authorization: `Basic ${basic}`
            }
        });

        const tokenObj = tokenFromResponse(tokenResp.data);
        // get user profile to identify user id
        const meResp = await axios.get(`${BB_HOST}/learn/api/public/v1/users/me`, {
            headers: { Authorization: `Bearer ${tokenObj.access_token}` }
        });

        const user = meResp.data;
        const userId = user.id || user.userId || user.name || crypto.randomBytes(8).toString("hex");
        saveTokensFor(userId, tokenObj);

        // show minimal success page with instructions and userId
        return res.send(`
      <h3>Auth successful</h3>
      <p>User id: <strong>${userId}</strong></p>
      <p>Copy the user id and use it for testing.</p>
      <pre>access_token: (stored securely on server)</pre>
    `);
    } catch (err) {
        console.error("callback error", err.response?.data || err.message);
        return res.status(500).send("auth callback failed: " + (err.response?.data || err.message));
    }
});

// Test endpoints

// get current user by providing an access token (quick test)
app.get("/me", async (req, res) => {
    const token = req.query.token;
    if (!token) return res.status(400).send("Provide ?token= for quick test");
    try {
        const r = await axios.get(`${BB_HOST}/learn/api/public/v1/users/me`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        res.json(r.data);
    } catch (err) {
        res.status(500).send(err.response?.data || err.message);
    }
});

// get current user using stored tokens (recommended flow)
app.get("/me/user/:userId", async (req, res) => {
    try {
        const userId = req.params.userId;
        const access = await refreshIfNeeded(userId);
        const r = await axios.get(`${BB_HOST}/learn/api/public/v1/users/me`, {
            headers: { Authorization: `Bearer ${access}` }
        });
        res.json(r.data);
    } catch (err) {
        res.status(500).send(err.response?.data || err.message);
    }
});

// list courses for stored user
app.get("/courses", async (req, res) => {
    try {
        const userId = req.query.userId;
        if (!userId) return res.status(400).send("Provide ?userId=");
        const access = await refreshIfNeeded(userId);
        const r = await axios.get(`${BB_HOST}/learn/api/public/v1/courses`, {
            headers: { Authorization: `Bearer ${access}` }
        });
        res.json(r.data);
    } catch (err) {
        res.status(500).send(err.response?.data || err.message);
    }
});

// fetch course contents (example)
app.get("/courses/:courseId/contents", async (req, res) => {
    try {
        const userId = req.query.userId;
        if (!userId) return res.status(400).send("Provide ?userId=");
        const access = await refreshIfNeeded(userId);
        const courseId = req.params.courseId;
        const r = await axios.get(`${BB_HOST}/learn/api/public/v1/courses/${encodeURIComponent(courseId)}/contents`, {
            headers: { Authorization: `Bearer ${access}` }
        });
        res.json(r.data);
    } catch (err) {
        res.status(500).send(err.response?.data || err.message);
    }
});

// simple logout / delete tokens
app.post("/logout/:userId", (req, res) => {
    removeTokensFor(req.params.userId);
    res.json({ ok: true });
});

app.listen(PORT, () => console.log(`Server listening on ${PORT}`));

// index.js
const express = require("express");
const fetch = require("node-fetch");
require("dotenv").config();

const app = express();
const PORT = process.env.PORT || 3000;

const CLIENT_ID = process.env.CLIENT_ID;
const CLIENT_SECRET = process.env.CLIENT_SECRET;
const BB_HOST = "https://luminate.centennialcollege.ca";

// Step 1: redirect user to Blackboard login
app.get("/auth/start", (req, res) => {
    const redirectUri = encodeURIComponent(`${process.env.BASE_URL}/auth/callback`);
    const state = Math.random().toString(36).substring(2, 15);
    const url = `${BB_HOST}/learn/api/public/v1/oauth2/authorize?response_type=code&client_id=${CLIENT_ID}&redirect_uri=${redirectUri}&state=${state}`;
    res.redirect(url);
});

// Step 2: handle callback from Blackboard
app.get("/auth/callback", async (req, res) => {
    const code = req.query.code;
    if (!code) return res.status(400).send("Missing code");

    try {
        const tokenResp = await fetch(`${BB_HOST}/learn/api/public/v1/oauth2/token`, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization":
                    "Basic " + Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString("base64"),
            },
            body: new URLSearchParams({
                grant_type: "authorization_code",
                code,
                redirect_uri: `${process.env.BASE_URL}/auth/callback`,
            }),
        });
        const data = await tokenResp.json();
        res.json(data); // for now just show tokens in browser
    } catch (err) {
        res.status(500).send(err.message);
    }
});

app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

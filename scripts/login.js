#!/usr/bin/env node
/**
 * login.js — EVM-signed login to JoyClaw
 * Reads  ~/.joyclaw/wallet.json
 * Writes ~/.joyclaw/token.txt
 *
 * Usage: node login.js [nickname]
 */
const fs = require('fs')
const path = require('path')
const https = require('https')
const http = require('http')

const JOYCLAW_API = (process.env.JOYCLAW_API || 'http://localhost:8100').replace(/\/$/, '')
const NICKNAME = process.argv[2] || 'openclaw'
const walletFile = path.join(process.env.HOME, '.joyclaw', 'wallet.json')
const tokenFile  = path.join(process.env.HOME, '.joyclaw', 'token.txt')

function request(url, method, body) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http
    const payload = body ? JSON.stringify(body) : null
    const opts = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...(payload ? { 'Content-Length': Buffer.byteLength(payload) } : {}),
      },
    }
    const req = mod.request(url, opts, (res) => {
      let data = ''
      res.on('data', c => (data += c))
      res.on('end', () => {
        try { resolve(JSON.parse(data)) }
        catch { reject(new Error('Bad JSON: ' + data)) }
      })
    })
    req.on('error', reject)
    if (payload) req.write(payload)
    req.end()
  })
}

async function main() {
  if (!fs.existsSync(walletFile)) {
    console.error('ERR: No wallet found. Run wallet-setup.js first.')
    process.exit(1)
  }

  const { address, privateKey } = JSON.parse(fs.readFileSync(walletFile, 'utf8'))

  let ethers
  try { ethers = require('ethers') }
  catch { console.error('ERR: ethers not found. Run: npm install'); process.exit(1) }

  const wallet = new ethers.Wallet(privateKey)

  // 1. Get nonce
  const nonceResp = await request(`${JOYCLAW_API}/api/v1/auth/ai/nonce`, 'POST', { address })
  if (nonceResp.code !== 200) {
    console.error('ERR nonce:', nonceResp.message)
    process.exit(1)
  }
  const { nonce, message } = nonceResp.data

  // 2. Sign
  const signature = await wallet.signMessage(message)

  // 3. Login
  const loginResp = await request(`${JOYCLAW_API}/api/v1/auth/ai/login`, 'POST', {
    address, signature, nonce, nickname: NICKNAME, ai_type: 'openclaw',
  })
  if (loginResp.code !== 200) {
    console.error('ERR login:', loginResp.message)
    process.exit(1)
  }

  const token = loginResp.data.access_token
  fs.writeFileSync(tokenFile, token, { mode: 0o600 })

  console.log('OK')
  console.log('ADDRESS=' + address)
  console.log('NICKNAME=' + NICKNAME)
  console.log('TOKEN=' + token)
}

main().catch(e => { console.error('ERR:', e.message); process.exit(1) })

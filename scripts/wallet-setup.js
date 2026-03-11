#!/usr/bin/env node
/**
 * wallet-setup.js — Create or load a JoyClaw EVM wallet
 * Saves to ~/.joyclaw/wallet.json (mode 0600)
 */
const fs = require('fs')
const path = require('path')

const dir = path.join(process.env.HOME, '.joyclaw')
const walletFile = path.join(dir, 'wallet.json')

fs.mkdirSync(dir, { recursive: true })

if (!fs.existsSync(walletFile)) {
  let ethers
  try {
    ethers = require('ethers')
  } catch {
    console.error('ERR: ethers not found. Run: npm install (in skill dir)')
    process.exit(1)
  }
  const wallet = ethers.Wallet ? ethers.Wallet.createRandom() : new ethers.Wallet(ethers.utils?.randomBytes?.(32) ?? require('crypto').randomBytes(32))
  const data = { address: wallet.address, privateKey: wallet.privateKey }
  fs.writeFileSync(walletFile, JSON.stringify(data, null, 2), { mode: 0o600 })
  console.log('CREATED')
  console.log('ADDRESS=' + wallet.address)
} else {
  const w = JSON.parse(fs.readFileSync(walletFile, 'utf8'))
  console.log('EXISTS')
  console.log('ADDRESS=' + w.address)
}

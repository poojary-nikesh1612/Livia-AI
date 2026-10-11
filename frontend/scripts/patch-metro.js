// scripts/patch-metro.js
// Fixes Metro 0.84.x incompatibility with Node.js 22+ strict ESM exports.
// Metro's package.json does not declare all internal subpaths it uses,
// causing ERR_PACKAGE_PATH_NOT_EXPORTED on Node 22.
// This script adds the required subpath mappings after npm install.

const fs = require('fs');
const path = require('path');

const metroPackagePath = path.join(__dirname, '..', 'node_modules', 'metro', 'package.json');

if (!fs.existsSync(metroPackagePath)) {
  console.log('metro not found — skipping patch');
  process.exit(0);
}

const pkg = JSON.parse(fs.readFileSync(metroPackagePath, 'utf8'));

// Only patch if the problematic path is not already defined
if (!pkg.exports['./src/DeltaBundler/Serializers/helpers/js']) {
  const additions = {
    './src/DeltaBundler/Serializers/helpers/js': './src/DeltaBundler/Serializers/helpers/js.js',
    './src/DeltaBundler/Serializers/helpers/*': './src/DeltaBundler/Serializers/helpers/*.js',
    './src/DeltaBundler/Serializers/*': './src/DeltaBundler/Serializers/*.js',
    './src/DeltaBundler/*': './src/DeltaBundler/*.js',
    './src/node-haste/*': './src/node-haste/*.js',
    './src/*': './src/*.js',
  };

  pkg.exports = { ...pkg.exports, ...additions };
  fs.writeFileSync(metroPackagePath, JSON.stringify(pkg, null, 2));
  console.log('✅ Patched metro/package.json for Node.js 22 compatibility');
} else {
  console.log('ℹ️ metro already patched — skipping');
}


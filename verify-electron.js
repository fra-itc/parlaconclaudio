/**
 * Verification script for Electron setup
 * Run with: node verify-electron.js
 */

const fs = require('fs');
const path = require('path');

const checks = [];

// Check if required files exist
const requiredFiles = [
  'src/ui/desktop/main.js',
  'src/ui/desktop/preload.js',
  'src/ui/desktop/renderer/index.html',
  'package.json',
  'vite.config.ts',
];

console.log('🔍 Verifying Electron setup...\n');

// File existence checks
requiredFiles.forEach(file => {
  const exists = fs.existsSync(path.join(__dirname, file));
  checks.push({ name: `File: ${file}`, passed: exists });
  console.log(exists ? '✅' : '❌', file);
});

console.log('\n📦 Checking package.json configuration...\n');

// Check package.json
try {
  const pkg = JSON.parse(fs.readFileSync(path.join(__dirname, 'package.json'), 'utf8'));

  const mainCorrect = pkg.main === 'src/ui/desktop/main.js';
  checks.push({ name: 'package.json main field', passed: mainCorrect });
  console.log(mainCorrect ? '✅' : '❌', 'main field:', pkg.main);

  const hasElectron = pkg.devDependencies?.electron !== undefined;
  checks.push({ name: 'electron dependency', passed: hasElectron });
  console.log(hasElectron ? '✅' : '❌', 'electron:', pkg.devDependencies?.electron || 'not found');

  const hasBuilder = pkg.devDependencies?.['electron-builder'] !== undefined;
  checks.push({ name: 'electron-builder dependency', passed: hasBuilder });
  console.log(hasBuilder ? '✅' : '❌', 'electron-builder:', pkg.devDependencies?.['electron-builder'] || 'not found');

  const hasStartScript = pkg.scripts?.start === 'electron .';
  checks.push({ name: 'start script', passed: hasStartScript });
  console.log(hasStartScript ? '✅' : '❌', 'start script:', pkg.scripts?.start || 'not found');

  const hasConcurrently = pkg.devDependencies?.concurrently !== undefined;
  checks.push({ name: 'concurrently dependency', passed: hasConcurrently });
  console.log(hasConcurrently ? '✅' : '❌', 'concurrently:', pkg.devDependencies?.concurrently || 'not found');

  const hasCrossEnv = pkg.devDependencies?.['cross-env'] !== undefined;
  checks.push({ name: 'cross-env dependency', passed: hasCrossEnv });
  console.log(hasCrossEnv ? '✅' : '❌', 'cross-env:', pkg.devDependencies?.['cross-env'] || 'not found');

} catch (error) {
  console.error('❌ Error reading package.json:', error.message);
  checks.push({ name: 'package.json readable', passed: false });
}

console.log('\n🔧 Checking main.js configuration...\n');

// Check main.js
try {
  const mainJs = fs.readFileSync(path.join(__dirname, 'src/ui/desktop/main.js'), 'utf8');

  const hasBrowserWindow = mainJs.includes('BrowserWindow');
  checks.push({ name: 'BrowserWindow in main.js', passed: hasBrowserWindow });
  console.log(hasBrowserWindow ? '✅' : '❌', 'BrowserWindow imported');

  const hasTray = mainJs.includes('Tray');
  checks.push({ name: 'Tray in main.js', passed: hasTray });
  console.log(hasTray ? '✅' : '❌', 'Tray imported');

  const hasIpcMain = mainJs.includes('ipcMain');
  checks.push({ name: 'ipcMain in main.js', passed: hasIpcMain });
  console.log(hasIpcMain ? '✅' : '❌', 'ipcMain imported');

  const hasPreload = mainJs.includes('preload:');
  checks.push({ name: 'preload script configured', passed: hasPreload });
  console.log(hasPreload ? '✅' : '❌', 'preload script reference');

  const hasContextIsolation = mainJs.includes('contextIsolation: true');
  checks.push({ name: 'contextIsolation enabled', passed: hasContextIsolation });
  console.log(hasContextIsolation ? '✅' : '❌', 'contextIsolation: true');

} catch (error) {
  console.error('❌ Error reading main.js:', error.message);
  checks.push({ name: 'main.js readable', passed: false });
}

console.log('\n🌉 Checking preload.js configuration...\n');

// Check preload.js
try {
  const preloadJs = fs.readFileSync(path.join(__dirname, 'src/ui/desktop/preload.js'), 'utf8');

  const hasContextBridge = preloadJs.includes('contextBridge');
  checks.push({ name: 'contextBridge in preload.js', passed: hasContextBridge });
  console.log(hasContextBridge ? '✅' : '❌', 'contextBridge imported');

  const hasExposeInMainWorld = preloadJs.includes('exposeInMainWorld');
  checks.push({ name: 'exposeInMainWorld used', passed: hasExposeInMainWorld });
  console.log(hasExposeInMainWorld ? '✅' : '❌', 'exposeInMainWorld called');

  const hasElectronAPI = preloadJs.includes("'electronAPI'");
  checks.push({ name: 'electronAPI exposed', passed: hasElectronAPI });
  console.log(hasElectronAPI ? '✅' : '❌', 'electronAPI exposed');

  const hasRecordingAPI = preloadJs.includes('recording:');
  checks.push({ name: 'recording API defined', passed: hasRecordingAPI });
  console.log(hasRecordingAPI ? '✅' : '❌', 'recording API');

} catch (error) {
  console.error('❌ Error reading preload.js:', error.message);
  checks.push({ name: 'preload.js readable', passed: false });
}

console.log('\n📊 Summary:\n');

const passed = checks.filter(c => c.passed).length;
const total = checks.length;
const percentage = Math.round((passed / total) * 100);

console.log(`✅ Passed: ${passed}/${total} (${percentage}%)`);
console.log(`❌ Failed: ${total - passed}/${total}`);

if (passed === total) {
  console.log('\n🎉 All checks passed! Electron setup is complete.');
  console.log('\n📝 Next steps:');
  console.log('   1. Run "npm start" to launch Electron app');
  console.log('   2. Or run "npm run dev" for development with hot reload');
  console.log('   3. Add icon files to assets/ directory for production build');
  console.log('   4. Implement actual audio recording and transcription logic');
} else {
  console.log('\n⚠️  Some checks failed. Please review the output above.');
  process.exit(1);
}

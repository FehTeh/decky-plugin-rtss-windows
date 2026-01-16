import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'));
const version = packageJson.version;
const pluginName = packageJson.name;
const zipName = `${pluginName}-v${version}.zip`;

// Create temporary directory structure
const tempDir = 'temp_dist';
const pluginDir = path.join(tempDir, pluginName);

if (fs.existsSync(tempDir)) {
    fs.rmSync(tempDir, { recursive: true, force: true });
}
fs.mkdirSync(pluginDir, { recursive: true });

// Copy required files into the plugin directory
const filesToCopy = ['package.json', 'plugin.json', 'main.py', 'README.md', 'LICENSE'];
filesToCopy.forEach(file => {
    if (fs.existsSync(file)) {
        fs.copyFileSync(file, path.join(pluginDir, file));
    }
});

// Copy dist directory
if (fs.existsSync('dist')) {
    fs.cpSync('dist', path.join(pluginDir, 'dist'), { recursive: true });
}

// Create zip from the plugin directory using bestzip
if (fs.existsSync(zipName)) {
    fs.unlinkSync(zipName);
}

execSync(`npx bestzip ${zipName} ${pluginDir}`, { stdio: 'inherit' });

// Clean up
fs.rmSync(tempDir, { recursive: true, force: true });

console.log(`Created ${zipName}`);
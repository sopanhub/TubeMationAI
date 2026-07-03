import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// Helper to parse .env file content
function parseEnv(content) {
  const result = {};
  const lines = content.split('\n');
  for (const line of lines) {
    const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
    if (match) {
      const key = match[1];
      let value = match[2] || '';
      value = value.trim().replace(/^["']|["']$/g, '');
      result[key] = value;
    }
  }
  return result;
}

export async function GET() {
  try {
    const envPath = path.join(process.cwd(), '.env');
    let envContent = '';
    
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    } else {
      // Create empty .env if it doesn't exist
      fs.writeFileSync(envPath, '', 'utf8');
    }

    const parsed = parseEnv(envContent);
    
    // Define the keys we care about
    const targetKeys = [
      'GEMINI_API_KEY',
      'GROQ_API_KEY',
      'YOUTUBE_CLIENT_ID',
      'YOUTUBE_CLIENT_SECRET',
      'YOUTUBE_REFRESH_TOKEN'
    ];

    const settings = {};
    for (const key of targetKeys) {
      // For security, only return whether it's set (true/false)
      settings[key] = !!parsed[key] && parsed[key].trim().length > 0;
    }

    return NextResponse.json({ settings });
  } catch (error) {
    console.error('Failed to read settings:', error);
    return NextResponse.json({ error: 'Failed to read settings' }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const updates = await request.json();
    const envPath = path.join(process.cwd(), '.env');
    
    let envContent = '';
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }

    const lines = envContent.split('\n');
    const newLines = [];
    const keysUpdated = new Set();

    for (const line of lines) {
      const match = line.match(/^\s*([\w.-]+)\s*=\s*(.*)?\s*$/);
      if (match) {
        const key = match[1];
        if (updates.hasOwnProperty(key)) {
          // Update the line if the key is in our updates
          // Only update if the user actually provided a value (we don't clear keys if they send empty, unless we want them to be able to clear. Let's allow clearing if they send an explicitly empty string)
          if (updates[key] !== undefined) {
             newLines.push(`${key}=${updates[key]}`);
             keysUpdated.add(key);
          } else {
             newLines.push(line); // keep original
          }
        } else {
          newLines.push(line);
        }
      } else {
        newLines.push(line);
      }
    }

    // Append any keys that were not in the file originally
    for (const [key, value] of Object.entries(updates)) {
      if (!keysUpdated.has(key) && value !== undefined) {
        newLines.push(`${key}=${value}`);
      }
    }

    fs.writeFileSync(envPath, newLines.join('\n'), 'utf8');
    
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to update settings:', error);
    return NextResponse.json({ error: 'Failed to update settings' }, { status: 500 });
  }
}

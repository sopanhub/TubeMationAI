import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

function isLikelyUrl(value) {
  try {
    const u = new URL(value);
    return u.protocol === 'http:' || u.protocol === 'https:';
  } catch {
    return false;
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { url, gameplayUrl, quality } = body || {};

    if (!url || !isLikelyUrl(url)) {
      return NextResponse.json({ error: 'Provide a valid main video URL.' }, { status: 400 });
    }

    const scriptPath = path.join(process.cwd(), 'scripts', 'mrbeast_generator.py');
    const lofiPath = path.join(process.cwd(), 'scripts', 'lofi.mp3');

    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        const args = ['-u', scriptPath, '--url', url];
        if (gameplayUrl && isLikelyUrl(gameplayUrl)) {
          args.push('--gameplay-url', gameplayUrl);
        }
        if (quality) {
          args.push('--quality', quality);
        }
        
        const child = spawn('python3', args, {
          env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
        });

        const sendJSON = (obj) => {
          controller.enqueue(encoder.encode(JSON.stringify(obj) + '\n'));
        };

        child.stdout.on('data', (data) => {
          const lines = data.toString().split('\n').filter(Boolean);
          for (const line of lines) {
            sendJSON({ type: 'log', message: line.trim() });
          }
        });

        child.stderr.on('data', (data) => {
          const lines = data.toString().split('\n').filter(Boolean);
          for (const line of lines) {
            console.error('[mrbeast-py-err]', line);
            sendJSON({ type: 'log', message: `[stderr] ${line.trim()}` });
          }
        });

        child.on('close', (code) => {
          if (code === 0) {
            sendJSON({ type: 'success', message: 'Short generation complete.' });
          } else {
            sendJSON({ type: 'error', message: `Process exited with code ${code}` });
          }
          controller.close();
        });

        child.on('error', (err) => {
          sendJSON({ type: 'error', message: `Failed to start Python script: ${err.message}` });
          controller.close();
        });
      },
    });

    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Transfer-Encoding': 'chunked',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    });
  } catch (err) {
    return NextResponse.json(
      { error: 'Server error processing request', details: err.message },
      { status: 500 }
    );
  }
}

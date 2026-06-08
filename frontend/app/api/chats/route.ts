import { NextResponse } from 'next/server';

function backendUrl(path: string) {
  const base = process.env.BACKEND_URL?.replace(/\/generate$/, '') ?? 'http://localhost:8000';
  return `${base}${path}`;
}

function forwardHeaders(req: Request): Record<string, string> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const auth = req.headers.get('authorization');
  if (auth) headers['Authorization'] = auth;
  return headers;
}

export async function GET(req: Request) {
  try {
    const res = await fetch(backendUrl('/chats'), { headers: forwardHeaders(req) });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Service unavailable' }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const res = await fetch(backendUrl('/chats'), {
      method: 'POST',
      headers: forwardHeaders(req),
    });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Service unavailable' }, { status: 500 });
  }
}

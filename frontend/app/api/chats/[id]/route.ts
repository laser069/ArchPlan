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

type Params = { params: Promise<{ id: string }> };

export async function GET(req: Request, { params }: Params) {
  const { id } = await params;
  try {
    const res = await fetch(backendUrl(`/chats/${id}`), { headers: forwardHeaders(req) });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Service unavailable' }, { status: 500 });
  }
}

export async function PATCH(req: Request, { params }: Params) {
  const { id } = await params;
  try {
    const body = await req.json();
    const res = await fetch(backendUrl(`/chats/${id}`), {
      method: 'PATCH',
      headers: forwardHeaders(req),
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Service unavailable' }, { status: 500 });
  }
}

export async function DELETE(req: Request, { params }: Params) {
  const { id } = await params;
  try {
    const res = await fetch(backendUrl(`/chats/${id}`), {
      method: 'DELETE',
      headers: forwardHeaders(req),
    });
    const data = await res.json().catch(() => ({ detail: res.statusText }));
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ error: 'Service unavailable' }, { status: 500 });
  }
}

import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();

    // The backend URL must be provided via environment variable.
    // Fail explicitly instead of silently falling back to localhost in production.
    const BACKEND_URL = process.env.BACKEND_URL;
    if (!BACKEND_URL) {
      throw new Error('BACKEND_URL environment variable is not set');
    }

    // FIXED: forward incoming Authorization header to backend
    const authHeader = req.headers.get('authorization');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (authHeader) headers['Authorization'] = authHeader;

    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      // Pass through the specific error status from the backend if available
      return NextResponse.json(
        { error: `Backend returned ${response.status}` }, 
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Return the data directly to the frontend hook
    return NextResponse.json(data);

  } catch (error) {
    // Log the error server-side for debugging, keep it clean for the client
    console.error('Architecture Generation Error:', error);
    
    return NextResponse.json(
      { error: 'Service temporarily unavailable' }, 
      { status: 500 }
    );
  }
}
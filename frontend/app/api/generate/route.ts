import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();

    // The backend URL should ideally be an environment variable
    const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000/generate';

    const response = await fetch(BACKEND_URL, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json' 
      },
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
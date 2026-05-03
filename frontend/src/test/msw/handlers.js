import { http, HttpResponse } from 'msw';

export const handlers = [
  // ── Auth ──────────────────────────────────────────────────────
  http.post('http://localhost:8000/api/auth/login/', async ({ request }) => {
    const body = await request.json();
    if (body?.password === 'wrong') {
      return HttpResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 },
      );
    }
    return HttpResponse.json(
      { access: 'fake-access-token', refresh: 'fake-refresh-token' },
      { status: 200 },
    );
  }),

  http.get('http://localhost:8000/api/auth/me/', ({ request }) => {
    const auth = request.headers.get('Authorization');
    if (!auth) {
      return HttpResponse.json(
        { error: 'Not authenticated' },
        { status: 401 },
      );
    }
    return HttpResponse.json(
      { id: 1, email: 'test@example.com', role: 'manager' },
    );
  }),

  http.post('http://localhost:8000/api/auth/logout/', () => {
    return HttpResponse.json({ detail: 'Logged out' });
  }),
];

/**
 * Integration tests for capture.js — real HTTP calls intercepted by MSW.
 * No vi.mock() — exercises the full axios → MSW round-trip.
 */
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { server } from '../test/msw/server';
import { createInspection, createDefect, closeInspection } from './capture';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => {
  server.resetHandlers();
  localStorage.clear();
});
afterAll(() => server.close());

const inspectionPayload = {
  lot: 'LOT-001',
  style: 'N6165',
  size: 'M',
  color: 'Red',
};

const defectPayload = {
  inspection: 42,
  defect_type: 'Seam',
  defect_size: 'Small',
  coordinates_x: [10, 20],
  coordinates_y: [30, 40],
  defect_count: 2,
};

describe('capture integration — createInspection', () => {
  it('sends POST body and returns inspection with ID', async () => {
    localStorage.setItem('rift-access-token', 'valid-token');

    const result = await createInspection(inspectionPayload);

    expect(result).toMatchObject({
      id: 42,
      lot: 'LOT-001',
      style: 'N6165',
      size: 'M',
      color: 'Red',
    });
  });

  it('fails with 401 when no auth token is present', async () => {
    await expect(createInspection(inspectionPayload)).rejects.toThrow();
  });
});

describe('capture integration — createDefect', () => {
  it('sends correct defect data with coordinates and returns defect', async () => {
    localStorage.setItem('rift-access-token', 'valid-token');

    const result = await createDefect(defectPayload);

    expect(result).toMatchObject({
      id: 1,
      inspection: 42,
      defect_type: 'Seam',
      coordinates_x: [10, 20],
      coordinates_y: [30, 40],
      defect_count: 2,
    });
  });
});

describe('capture integration — closeInspection', () => {
  it('calls the correct URL with ID and returns PASS result', async () => {
    localStorage.setItem('rift-access-token', 'valid-token');

    const result = await closeInspection(42);

    expect(result).toEqual({
      id: 42,
      status: 'closed',
      result: 'PASS',
    });
  });
});

describe('capture integration — full end-to-end flow', () => {
  it('creates inspection → creates defect → closes inspection', async () => {
    localStorage.setItem('rift-access-token', 'valid-token');

    // Step 1: Create inspection
    const inspection = await createInspection(inspectionPayload);
    expect(inspection.id).toBe(42);

    // Step 2: Create defect linked to the inspection
    const defect = await createDefect({ ...defectPayload, inspection: inspection.id });
    expect(defect.id).toBe(1);
    expect(defect.inspection).toBe(42);

    // Step 3: Close the inspection
    const closeResult = await closeInspection(inspection.id);
    expect(closeResult).toMatchObject({
      id: 42,
      status: 'closed',
      result: 'PASS',
    });
  });
});

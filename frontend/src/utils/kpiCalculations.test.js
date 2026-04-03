import { describe, it, expect } from 'vitest';
import {
  calculateAqlByStyle,
  calculateAqlWeekly,
  calculateAuditedPieces,
  calculateAcReRateByLine,
  calculateSecondsRework,
  calculatePerformanceByCustomer,
  calculatePerformanceByLine,
  calculateTopDefects,
  calculateFabricDefects,
  calculateDefectsByStyleType,
  calculatePassRejectDistribution,
  calculateRejectedEvolution,
  calculateContainersByState,
  calculateDefectRate,
} from './kpiCalculations.js';

// ─── Shared test fixtures ─────────────────────────────────────────────────────

/** Minimal valid row set covering all used fields. */
const SAMPLE_ROWS = [
  {
    week: '1',
    team: 'Linea A',
    style: 'Style-X',
    customer: 'Cliente-1',
    color: 'Rojo',
    qty: 100,
    accepted: 90,
    rejected: 10,
    sample: 100,
    defects_total: 12,
    pass_or_fail: 'PASS',
    date_1: '2026-01-01',
  },
  {
    week: '1',
    team: 'Linea A',
    style: 'Style-X',
    customer: 'Cliente-1',
    color: 'Azul',
    qty: 50,
    accepted: 45,
    rejected: 5,
    sample: 50,
    defects_total: 5,
    pass_or_fail: 'PASS',
    date_1: '2026-01-02',
  },
  {
    week: '2',
    team: 'Linea B',
    style: 'Style-Y',
    customer: 'Cliente-2',
    color: 'Verde',
    qty: 80,
    accepted: 60,
    rejected: 20,
    sample: 80,
    defects_total: 20,
    pass_or_fail: 'REJECT',
    date_1: '2026-01-09',
  },
  {
    week: '2',
    team: 'Linea B',
    style: 'Style-Y',
    customer: 'Cliente-2',
    color: 'Amarillo',
    qty: 40,
    accepted: 38,
    rejected: 2,
    sample: 40,
    defects_total: 2,
    pass_or_fail: 'PASS',
    date_1: '2026-01-10',
  },
  {
    week: '2',
    team: 'Linea A',
    style: 'Style-X',
    customer: 'Cliente-1',
    color: 'Rojo',
    qty: 60,
    accepted: 50,
    rejected: 10,
    sample: 60,
    defects_total: 10,
    pass_or_fail: 'REJECT',
    date_1: '2026-01-11',
  },
];

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('calculateAqlByStyle', () => {
  it('computes defects/sample*100 grouped by style', () => {
    const result = calculateAqlByStyle(SAMPLE_ROWS);
    const styleX = result.find((r) => r.style === 'Style-X');
    expect(styleX).toBeDefined();
    // Style-X: (12+5+10) / (100+50+60)*100 = 27/210*100 ≈ 12.857
    expect(styleX.aql).toBeCloseTo(12.857, 2);
  });

  it('handles empty array', () => {
    expect(calculateAqlByStyle([])).toEqual([]);
  });

  it('handles missing fields gracefully', () => {
    const result = calculateAqlByStyle([{ style: 'S1' }]);
    expect(result).toHaveLength(1);
    expect(result[0].aql).toBe(0);
  });
});

describe('calculateAqlWeekly', () => {
  it('computes weekly AQL sorted by week', () => {
    const result = calculateAqlWeekly(SAMPLE_ROWS);
    expect(result).toHaveLength(2);
    expect(result[0].week).toBe('1');
    // Week 1: (12+5)/(100+50)*100 = 17/150*100 ≈ 11.333
    expect(result[0].aql).toBeCloseTo(11.333, 2);
    // Week 2: (20+2+10)/(80+40+60)*100 = 32/180*100 ≈ 17.778
    expect(result[1].aql).toBeCloseTo(17.778, 2);
  });

  it('handles empty array', () => {
    expect(calculateAqlWeekly([])).toEqual([]);
  });
});

describe('calculateAuditedPieces', () => {
  it('sums sample field per week', () => {
    const result = calculateAuditedPieces(SAMPLE_ROWS);
    const w1 = result.find((r) => r.week === '1');
    const w2 = result.find((r) => r.week === '2');
    expect(w1.pieces).toBe(150);   // 100 + 50
    expect(w2.pieces).toBe(180);  // 80 + 40 + 60
  });

  it('handles empty array', () => {
    expect(calculateAuditedPieces([])).toEqual([]);
  });
});

describe('calculateAcReRateByLine', () => {
  it('computes pass rate per team', () => {
    const result = calculateAcReRateByLine(SAMPLE_ROWS);
    const lineaA = result.find((r) => r.line === 'Linea A');
    expect(lineaA).toBeDefined();
    // Linea A: accepted=90+45+50=185, rejected=10+5+10=25, total=210
    // passRate = 185/210*100 ≈ 88.095
    expect(lineaA.passRate).toBeCloseTo(88.095, 2);
    expect(lineaA.accepted).toBe(185);
    expect(lineaA.rejected).toBe(25);
  });

  it('handles empty array', () => {
    expect(calculateAcReRateByLine([])).toEqual([]);
  });
});

describe('calculateSecondsRework', () => {
  it('returns null (not available in Excel volatile mode)', () => {
    expect(calculateSecondsRework(SAMPLE_ROWS)).toBeNull();
    expect(calculateSecondsRework([])).toBeNull();
  });
});

describe('calculatePerformanceByCustomer', () => {
  it('computes accepted/sample*100 per customer', () => {
    const result = calculatePerformanceByCustomer(SAMPLE_ROWS);
    const c1 = result.find((r) => r.customer === 'Cliente-1');
    const c2 = result.find((r) => r.customer === 'Cliente-2');
    // Cliente-1: accepted=90+45+50=185, sample=100+50+60=210 → 88.095
    expect(c1.performance).toBeCloseTo(88.095, 2);
    // Cliente-2: accepted=60+38=98, sample=80+40=120 → 81.667
    expect(c2.performance).toBeCloseTo(81.667, 2);
  });

  it('handles empty array', () => {
    expect(calculatePerformanceByCustomer([])).toEqual([]);
  });
});

describe('calculatePerformanceByLine', () => {
  it('computes accepted/sample*100 per team', () => {
    const result = calculatePerformanceByLine(SAMPLE_ROWS);
    const lineaB = result.find((r) => r.line === 'Linea B');
    expect(lineaB).toBeDefined();
    // Linea B: accepted=60+38=98, sample=80+40=120 → 81.667
    expect(lineaB.performance).toBeCloseTo(81.667, 2);
  });

  it('handles empty array', () => {
    expect(calculatePerformanceByLine([])).toEqual([]);
  });
});

describe('calculateTopDefects', () => {
  it('returns single Total Defectos bucket with sum of defects_total', () => {
    const result = calculateTopDefects(SAMPLE_ROWS);
    expect(result).toHaveLength(1);
    expect(result[0].defectType).toBe('Total Defectos');
    // 12 + 5 + 20 + 2 + 10 = 49
    expect(result[0].count).toBe(49);
  });

  it('handles empty array', () => {
    const result = calculateTopDefects([]);
    expect(result).toHaveLength(1);
    expect(result[0].count).toBe(0);
  });
});

describe('calculateFabricDefects', () => {
  it('returns null (not available in Excel volatile mode)', () => {
    expect(calculateFabricDefects(SAMPLE_ROWS)).toBeNull();
    expect(calculateFabricDefects([])).toBeNull();
  });
});

describe('calculateDefectsByStyleType', () => {
  it('returns null (not available in Excel volatile mode)', () => {
    expect(calculateDefectsByStyleType(SAMPLE_ROWS)).toBeNull();
    expect(calculateDefectsByStyleType([])).toBeNull();
  });
});

describe('calculatePassRejectDistribution', () => {
  it('counts PASS vs REJECT rows', () => {
    const result = calculatePassRejectDistribution(SAMPLE_ROWS);
    const pass = result.find((r) => r.name === 'PASS');
    const reject = result.find((r) => r.name === 'REJECT');
    expect(pass.value).toBe(3);   // 3 PASS rows
    expect(reject.value).toBe(2); // 2 REJECT rows
  });

  it('handles empty array', () => {
    expect(calculatePassRejectDistribution([])).toEqual([]);
  });
});

describe('calculateRejectedEvolution', () => {
  it('sums rejected per week', () => {
    const result = calculateRejectedEvolution(SAMPLE_ROWS);
    const w1 = result.find((r) => r.week === '1');
    const w2 = result.find((r) => r.week === '2');
    expect(w1.rejected).toBe(15);  // 10 + 5
    expect(w2.rejected).toBe(32);  // 20 + 2 + 10
  });

  it('handles empty array', () => {
    expect(calculateRejectedEvolution([])).toEqual([]);
  });
});

describe('calculateContainersByState', () => {
  it('returns null (not available in Excel volatile mode)', () => {
    expect(calculateContainersByState(SAMPLE_ROWS)).toBeNull();
    expect(calculateContainersByState([])).toBeNull();
  });
});

describe('calculateDefectRate', () => {
  it('computes total defects / total sample * 100', () => {
    const result = calculateDefectRate(SAMPLE_ROWS);
    // Total defects = 12+5+20+2+10 = 49
    // Total sample  = 100+50+80+40+60 = 330
    // Defect rate = 49/330*100 ≈ 14.8485
    expect(result).toBeCloseTo(14.8485, 2);
  });

  it('handles empty array', () => {
    expect(calculateDefectRate([])).toBe(0);
  });

  it('skips rows with zero sample', () => {
    const result = calculateDefectRate([{ defects_total: 5, sample: 0 }]);
    expect(result).toBe(0);
  });
});

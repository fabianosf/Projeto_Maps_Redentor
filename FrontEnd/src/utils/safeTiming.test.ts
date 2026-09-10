import { describe, expect, it } from 'vitest';
import {
  isThirdPartyStartTimeNoise,
  readPerformanceEntryStartTimes,
  readStartTime,
  readStartTimes,
} from './safeTiming';

describe('safeTiming', () => {
  it('não lê startTime de undefined/null', () => {
    expect(readStartTime(undefined)).toBeNull();
    expect(readStartTime(null)).toBeNull();
    expect(readStartTime({})).toBeNull();
    expect(readStartTime({ startTime: Number.NaN })).toBeNull();
    expect(
      readStartTimes([undefined, null, { startTime: 10 }, { startTime: undefined }]),
    ).toEqual([10]);
  });

  it('readPerformanceEntryStartTimes ignora entradas ausentes', () => {
    expect(readPerformanceEntryStartTimes(undefined)).toEqual([]);
    expect(readPerformanceEntryStartTimes([undefined, null])).toEqual([]);
    expect(
      readPerformanceEntryStartTimes([
        undefined,
        { startTime: 1.5 } as PerformanceEntry,
        { startTime: Number.NaN } as PerformanceEntry,
      ]),
    ).toEqual([1.5]);
  });

  it('detecta ruído de extensão/VM sem stack do app', () => {
    expect(
      isThirdPartyStartTimeNoise(
        "Cannot read properties of undefined (reading 'startTime')",
        'at reportAllChanges (VM104:2:1134)',
      ),
    ).toBe(true);
    expect(
      isThirdPartyStartTimeNoise(
        "Cannot read properties of undefined (reading 'startTime')",
        'at foo (http://localhost:5173/src/screens/mapa/MapaFormScreen.tsx:10:2)',
      ),
    ).toBe(false);
  });
});

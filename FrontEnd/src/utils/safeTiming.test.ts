import { describe, expect, it } from 'vitest';
import { readStartTime, readStartTimes } from '@/utils/safeTiming';

describe('safeTiming', () => {
  it('não lê startTime de undefined/null', () => {
    expect(readStartTime(undefined)).toBeNull();
    expect(readStartTime(null)).toBeNull();
    expect(readStartTime({})).toBeNull();
  });

  it('ignora itens undefined na lista', () => {
    expect(
      readStartTimes([undefined, null, { startTime: 10 }, { startTime: undefined }]),
    ).toEqual([10]);
  });
});

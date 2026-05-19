import { test } from 'node:test';
import assert from 'node:assert';
import { intensityToGutterColor } from './heatmapUtils.js';

test('intensityToGutterColor handles intensity <= 0', () => {
    assert.strictEqual(intensityToGutterColor(-0.5), 'transparent');
    assert.strictEqual(intensityToGutterColor(0), 'transparent');
});

test('intensityToGutterColor handles low intensity (Green)', () => {
    // rgba(34, 197, 94, ${(0.3 + intensity * 0.4).toFixed(3)})
    assert.strictEqual(intensityToGutterColor(0.1), 'rgba(34, 197, 94, 0.340)');
    assert.strictEqual(intensityToGutterColor(0.349), 'rgba(34, 197, 94, 0.440)');
});

test('intensityToGutterColor handles medium intensity (Amber)', () => {
    // Exactly at threshold 0.35
    assert.strictEqual(intensityToGutterColor(0.35), 'rgba(245, 158, 11, 0.640)');
    // Between 0.35 and 0.65
    assert.strictEqual(intensityToGutterColor(0.5), 'rgba(245, 158, 11, 0.700)');
    assert.strictEqual(intensityToGutterColor(0.649), 'rgba(245, 158, 11, 0.760)');
});

test('intensityToGutterColor handles high intensity (Red)', () => {
    // Exactly at threshold 0.65
    assert.strictEqual(intensityToGutterColor(0.65), 'rgba(239, 68, 68, 0.895)');
    // Above 0.65
    assert.strictEqual(intensityToGutterColor(0.8), 'rgba(239, 68, 68, 0.940)');
    assert.strictEqual(intensityToGutterColor(1.0), 'rgba(239, 68, 68, 1.000)');
    // Above 1.0 should be clamped to 1.000 alpha
    assert.strictEqual(intensityToGutterColor(1.5), 'rgba(239, 68, 68, 1.000)');
});

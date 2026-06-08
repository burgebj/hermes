import test from 'node:test';
import assert from 'node:assert/strict';

import { shouldSyncHistoryMessage } from './history_sync.js';

test('keeps essential history sync types when full history download is disabled', () => {
  assert.equal(shouldSyncHistoryMessage({ syncType: 0 }), true);
  assert.equal(shouldSyncHistoryMessage({ syncType: 1 }), true);
  assert.equal(shouldSyncHistoryMessage({ syncType: 2 }), false);
  assert.equal(shouldSyncHistoryMessage({ syncType: 3 }), true);
});

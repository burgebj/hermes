// Baileys 7.x overrides the default history-sync callback to
// `() => !!syncFullHistory` when the caller does not provide one.
// Hermes wants to skip the full history download, but it still needs
// bootstrap / recent syncs for LID mappings and group participation.
export function shouldSyncHistoryMessage(sync) {
  return sync?.syncType !== 2;
}

import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  buildQuotedSendOptions,
  extractMessageText,
  extractQuoteContext,
  messageStore,
  rememberMessage,
  resolveStoredMessage,
} from './bridge.js';

const chatId = '5215514706713@s.whatsapp.net';
const statusAuthor = '5215559453922@s.whatsapp.net';

function textMessage(id, remoteJid = chatId, text = 'hola') {
  return {
    key: { id, remoteJid, fromMe: false },
    message: { conversation: text },
    messageTimestamp: 1710000000,
  };
}

test('message store resolves quoted messages by chat and message id', () => {
  messageStore.clear();
  const msg = textMessage('orig-1');

  rememberMessage(msg);

  assert.equal(resolveStoredMessage(chatId, 'orig-1'), msg);
});

test('quoted send options include Baileys quoted object when replyTo is found', () => {
  messageStore.clear();
  const msg = textMessage('orig-2');
  rememberMessage(msg);

  const options = buildQuotedSendOptions(chatId, 'orig-2');

  assert.deepEqual(options, { quoted: msg });
});

test('quoted send options degrade gracefully when replyTo is unknown', () => {
  messageStore.clear();

  const options = buildQuotedSendOptions(chatId, 'missing');

  assert.deepEqual(options, {});
});

test('extractQuoteContext exposes id, text, participant, and remote jid', () => {
  const content = {
    extendedTextMessage: {
      text: 'reply body',
      contextInfo: {
        stanzaId: 'quoted-1',
        participant: '5215000000000@s.whatsapp.net',
        remoteJid: 'status@broadcast',
        quotedMessage: {
          imageMessage: { caption: 'status caption' },
        },
      },
    },
  };

  assert.deepEqual(extractQuoteContext(content), {
    quotedMessageId: 'quoted-1',
    quotedParticipant: '5215000000000@s.whatsapp.net',
    quotedRemoteJid: 'status@broadcast',
    quotedText: 'status caption',
  });
});

test('extractMessageText handles common text and caption message shapes', () => {
  assert.equal(extractMessageText({ conversation: 'plain' }), 'plain');
  assert.equal(extractMessageText({ extendedTextMessage: { text: 'extended' } }), 'extended');
  assert.equal(extractMessageText({ imageMessage: { caption: 'image caption' } }), 'image caption');
});

test('status messages can be resolved from the store for private replies', () => {
  messageStore.clear();
  const status = textMessage('status-1', 'status@broadcast', 'new status');
  status.key.participant = statusAuthor;
  rememberMessage(status);

  assert.equal(resolveStoredMessage('status@broadcast', 'status-1'), status);
  assert.equal(resolveStoredMessage(statusAuthor, 'status-1'), undefined);
});

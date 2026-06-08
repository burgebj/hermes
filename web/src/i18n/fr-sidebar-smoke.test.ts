import { fr } from "./fr";

type Exact<Actual, Expected> = (<T>() => T extends Actual ? 1 : 2) extends <T>() =>
  T extends Expected ? 1 : 2
  ? (<T>() => T extends Expected ? 1 : 2) extends <T>() => T extends Actual ? 1 : 2
    ? true
    : false
  : false;
type Expect<T extends true> = T;

export const frenchSidebarNavCopy = {
  channels: fr.app.nav.channels,
  chat: fr.app.nav.chat,
  cron: fr.app.nav.cron,
  pairing: fr.app.nav.pairing,
  profiles: fr.app.nav.profiles,
  system: fr.app.nav.system,
  webhooks: fr.app.nav.webhooks,
};

export type FrenchSidebarNavCopySmoke = [
  Expect<Exact<typeof frenchSidebarNavCopy.channels, "Canaux">>,
  Expect<Exact<typeof frenchSidebarNavCopy.chat, "Discussion">>,
  Expect<Exact<typeof frenchSidebarNavCopy.cron, "Planification">>,
  Expect<Exact<typeof frenchSidebarNavCopy.pairing, "Appairage">>,
  Expect<Exact<typeof frenchSidebarNavCopy.profiles, "Profils">>,
  Expect<Exact<typeof frenchSidebarNavCopy.system, "Système">>,
  Expect<Exact<typeof frenchSidebarNavCopy.webhooks, "Webhooks">>,
];

export const frenchSidebarStatusCopy = {
  activeSessionsLabel: fr.app.activeSessionsLabel,
  gatewayRunning: fr.app.gatewayStrip.running,
  gatewayStatusLabel: fr.app.gatewayStatusLabel,
};

export type FrenchSidebarStatusCopySmoke = [
  Expect<Exact<typeof frenchSidebarStatusCopy.activeSessionsLabel, "Sessions actives :">>,
  Expect<Exact<typeof frenchSidebarStatusCopy.gatewayRunning, "En ligne">>,
  Expect<Exact<typeof frenchSidebarStatusCopy.gatewayStatusLabel, "Passerelle :">>,
];

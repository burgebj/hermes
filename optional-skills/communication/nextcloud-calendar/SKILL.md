---
name: nextcloud-calendar
description: Nextcloud Kalender via CalDAV. Termine abfragen, erstellen, aendern, loeschen. Erinnerungen (VALARM), Teilnehmer (ATTENDEE), wiederkehrende Termine (RRULE). Auch fuer Kalender-Event-Reaktionen (Cron-Usecase).
version: 1.0.0
author: niko
license: MIT
metadata:
  hermes:
    tags: [Nextcloud, Calendar, CalDAV]
prerequisites:
  commands: []
---

# Nextcloud Calendar — CalDAV

Hermes hat Zugriff auf Nextcloud-Kalender via CalDAV API. Termine koennen abgefragt, erstellt, geaendert und geloescht werden.

**WICHTIG:** Wenn du einen Termin FUER DEN USER erstellst, IMMER ATTENDEE setzen:
```
ORGANIZER;CN=Hermes:mailto:hermes@syringonline.de
ATTENDEE;CN=Niko;PARTSTAT=NEEDS-ACTION:mailto:nikolas@syringonline.de
```
Ohne ATTENDEE sieht der User den Termin NICHT — er landet nur in Hermes' eigenem Kalender.
Nur Termine die NUR fuer Hermes selbst sind (Cron-Tasks) brauchen keinen ATTENDEE.

Nutze das `terminal` Tool fuer alle Befehle. NICHT execute_code — das hat keinen Zugriff auf API-Keys.

## Authentifizierung

```python
import requests, uuid, os
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

# Credentials aus .env laden
env = {}
for line in open(os.path.expanduser("~/.hermes/.env")):
    if "=" in line and not line.startswith("#"):
        k, v = line.strip().split("=", 1)
        env[k] = v

NC_URL = "$NEXTCLOUD_URL"
NC_USER = "hermes"
NC_PASS = env.get("NEXTCLOUD_TALK_APP_PASSWORD", "")
DAV_BASE = f"{NC_URL}/remote.php/dav/calendars/{NC_USER}"
```

## Kalender auflisten

```python
resp = requests.request("PROPFIND", f"{DAV_BASE}/",
    auth=(NC_USER, NC_PASS),
    headers={"Depth": "1", "Content-Type": "application/xml"},
    data="""<?xml version="1.0"?>
    <d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
      <d:prop><d:displayname/><d:resourcetype/></d:prop>
    </d:propfind>""")

ns = {"d": "DAV:", "c": "urn:ietf:params:xml:ns:caldav"}
root = ET.fromstring(resp.text)
for r in root.findall("d:response", ns):
    name = r.findtext(".//d:displayname", "", ns)
    rt = r.find(".//d:resourcetype", ns)
    is_cal = rt is not None and rt.find("c:calendar", ns) is not None
    if is_cal:
        href = r.findtext("d:href", "", ns)
        print(f"{name}: {href}")
```

## Termine abfragen (Zeitraum)

```python
start = datetime.now(timezone.utc).strftime("%Y%m%dT000000Z")
end = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y%m%dT235959Z")

resp = requests.request("REPORT", f"{DAV_BASE}/personal/",
    auth=(NC_USER, NC_PASS),
    headers={"Depth": "1", "Content-Type": "application/xml"},
    data=f"""<?xml version="1.0"?>
    <c:calendar-query xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
      <d:prop><d:getetag/><c:calendar-data/></d:prop>
      <c:filter>
        <c:comp-filter name="VCALENDAR">
          <c:comp-filter name="VEVENT">
            <c:time-range start="{start}" end="{end}"/>
          </c:comp-filter>
        </c:comp-filter>
      </c:filter>
    </c:calendar-query>""")

# Antwort enthaelt calendar-data (iCalendar) pro Event
ns = {"d": "DAV:", "c": "urn:ietf:params:xml:ns:caldav"}
root = ET.fromstring(resp.text)
for r in root.findall("d:response", ns):
    cal_data = r.findtext(".//c:calendar-data", "", ns)
    if cal_data:
        print(cal_data)
```

Fuer andere Kalender (z.B. geteilte): Pfad `personal/` durch den Kalender-Pfad aus PROPFIND ersetzen.

## Termin erstellen

```python
uid = uuid.uuid4().hex
ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Hermes//Calendar//EN
BEGIN:VEVENT
UID:{uid}@hermes
DTSTART;TZID=Europe/Berlin:20260412T120000
DTEND;TZID=Europe/Berlin:20260412T130000
SUMMARY:Besuch bei Mutter
DESCRIPTION:Termin fuer Niko
BEGIN:VALARM
TRIGGER:-PT30M
ACTION:DISPLAY
DESCRIPTION:Erinnerung
END:VALARM
END:VEVENT
END:VCALENDAR"""

resp = requests.put(f"{DAV_BASE}/personal/{uid}.ics",
    auth=(NC_USER, NC_PASS),
    headers={"Content-Type": "text/calendar"},
    data=ics)
print(f"Status: {resp.status_code}")  # 201 = erstellt
```

## Termin mit Teilnehmer (fuer Niko sichtbar)

Fuege ORGANIZER und ATTENDEE zum VEVENT hinzu:

```
ORGANIZER;CN=Hermes:mailto:hermes@syringonline.de
ATTENDEE;CN=Niko;PARTSTAT=NEEDS-ACTION:mailto:nikolas@syringonline.de
```

Die mailto-Adressen muessen den echten Email-Adressen der NC-User entsprechen.

## Termin in geteiltem Kalender erstellen

Wenn Nikos Kalender mit Hermes geteilt ist, den Pfad per PROPFIND ermitteln und dort schreiben:

```python
resp = requests.put(f"{DAV_BASE}/shared-by-niko/{uid}.ics",
    auth=(NC_USER, NC_PASS),
    headers={"Content-Type": "text/calendar"},
    data=ics)
```

Den genauen Pfad des geteilten Kalenders per Kalender-Auflisten ermitteln.

## Zeitzonen

**WICHTIG:** User-Zeiten sind IMMER lokal (Europe/Berlin). IMMER `TZID` verwenden:

```
# Richtig:
DTSTART;TZID=Europe/Berlin:20260412T120000

# Falsch (2 Stunden Differenz im Sommer!):
DTSTART:20260412T120000Z
```

Wenn der User "12 Uhr" sagt, meint er 12:00 Europe/Berlin.

## Erinnerungen (VALARM)

VALARM-Block im VEVENT:

```
BEGIN:VALARM
TRIGGER:-PT30M
ACTION:DISPLAY
DESCRIPTION:Erinnerung
END:VALARM
```

Trigger-Werte: `-PT15M` (15 Min), `-PT1H` (1 Std), `-P1D` (1 Tag vorher).

## Wiederkehrende Termine (RRULE)

RRULE-Zeile im VEVENT, NC verwaltet Wiederholungen automatisch:

```
RRULE:FREQ=DAILY;COUNT=7           # Jeden Tag, 7 Mal
RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR   # Jeden Mo, Mi, Fr
RRULE:FREQ=MONTHLY;BYMONTHDAY=1    # Jeden 1. des Monats
RRULE:FREQ=HOURLY;INTERVAL=2       # Alle 2 Stunden
```

## Termin aendern

Zuerst GET fuer ETag, dann PUT mit If-Match:

```python
# 1. Event lesen
resp = requests.get(f"{DAV_BASE}/personal/{uid}.ics", auth=(NC_USER, NC_PASS))
etag = resp.headers.get("ETag")
original_ics = resp.text

# 2. ICS modifizieren (z.B. SUMMARY aendern) und zurueckschreiben
resp = requests.put(f"{DAV_BASE}/personal/{uid}.ics",
    auth=(NC_USER, NC_PASS),
    headers={"Content-Type": "text/calendar", "If-Match": etag},
    data=modified_ics)
# 204 = OK, 412 = ETag veraltet (parallel geaendert)
```

## Termin loeschen

```python
resp = requests.delete(f"{DAV_BASE}/personal/{uid}.ics", auth=(NC_USER, NC_PASS))
# 204 = geloescht
```

## Einzelnen Termin lesen

```python
resp = requests.get(f"{DAV_BASE}/personal/{uid}.ics", auth=(NC_USER, NC_PASS))
print(resp.text)  # iCalendar Format
```

## Reaktion auf Kalender-Events (Cron-Usecase)

Wenn du eine Notification fuer einen Kalender-Event bekommst:

1. Die Notification enthaelt bereits den Event-Inhalt (Summary, Description, Date)
2. Interpretiere die Beschreibung als Arbeitsauftrag und fuehre ihn aus
3. WICHTIG: Lade zuerst die benoetigten Skills fuer die Aufgabe:
   - Email-Aufgaben: skill_view("himalaya"), dann terminal mit himalaya CLI
   - Datei-Aufgaben: skill_view("nextcloud-files")
   - HA-Aufgaben: ha_get_state / ha_call_service oder skill_view("homeassistant-integration")
4. Nutze NIEMALS ein Tool namens "email" — das existiert nicht. Email geht IMMER ueber den himalaya Skill + terminal
5. Nach Ausfuehrung: Event loeschen oder STATUS:CANCELLED setzen

## Wichtig

- Zeitzonen: IMMER TZID=Europe/Berlin, NIE UTC fuer User-Termine
- Erinnerungen: NC-eigene VALARM nutzen, nicht selbst erinnern
- Geteilte Kalender: Pfad per PROPFIND ermitteln, nicht raten
- Aenderungen: IMMER ETag per GET holen und If-Match beim PUT setzen

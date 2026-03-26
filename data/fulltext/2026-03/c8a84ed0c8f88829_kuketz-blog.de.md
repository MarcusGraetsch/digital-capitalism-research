---
url: https://www.kuketz-blog.de/android-spyware-in-10-schritten-erkennen-und-entfernen/
title: Android-Spyware in 10 Schritten erkennen und entfernen • Kuketz IT-Security Blog
domain: kuketz-blog.de
category: privacy-security
source: rss
date_scanned: 2026-03-15T08:04:36.777749
word_count: 2160
paywall: False
---

# Android-Spyware in 10 Schritten erkennen und entfernen • Kuketz IT-Security Blog

**URL:** https://www.kuketz-blog.de/android-spyware-in-10-schritten-erkennen-und-entfernen/

**Domain:** kuketz-blog.de

**Category:** privacy-security

**Source:** RSS Feed

**Scanned:** 2026-03-15T08:04:36.777749

**Word Count:** 2160

---

Mike Kuketz

10. Februar 2026

Android-Spyware in 10 Schritten erkennen und entfernen

Android-Spyware ist selten der große »Hightech-Hack« – meistens ist es ein Angriff nach dem Motto: Gelegenheit macht Diebe. Ein paar Minuten Zugriff auf ein entsperrtes Gerät reichen, um eine Überwachungs-App zu installieren und ihr die nötigen Rechte zu geben. Danach läuft sie möglichst unauffällig im Hintergrund, tarnt sich mit harmlosen Namen und versucht, sich gegen Entfernung abzusichern. Wer einen konkreten Verdacht hat, sollte ruhig bleiben, aber strukturiert vorgehen. Genau dafür ist dieser kompakte Leitfaden gedacht.

Hinweis

Die folgenden Prüfpunkte ersetzen keine forensische Analyse: Gezielte Zero-Day-Angriffe, kompromittierte Firmware oder staatliche Spionage-Toolchains lassen sich mit den folgenden Checks in der Regel nicht zuverlässig erkennen. Wer also im Fokus steht oder ein entsprechend hohes Threat Model hat, sollte im Verdachtsfall eine professionelle forensische Analyse beauftragen.

Schritt 1: Erst klären, ob das System noch vertrauenswürdig ist

Bevor du in einzelnen Apps suchst, klärst du die Basis: Kannst du dem System überhaupt noch vertrauen? Ein sehr aussagekräftiger Hinweis ist eine Warnung direkt beim Start des Systems, zum Beispiel »Bootloader unlocked«, »Device can’t be checked for corruption« oder ein Symbol mit offenem Schloss. Das ist nicht automatisch »schlimm« – manche

entsperren den Bootloader

bewusst, etwa für Custom-ROMs oder Root. Für einen Spyware-Verdacht ist es aber relevant, weil ein entsperrter Bootloader Änderungen am System grundsätzlich erleichtert und du dann nicht mehr vom üblichen, abgesicherten Standardzustand ausgehen solltest. Wenn du so eine Warnung siehst, obwohl du nie bewusst etwas entsperrt oder modifiziert hast, ist das ein Warnsignal.

Danach prüfst du die App-Liste gezielt auf

Root-Spuren

¹: Magisk (inklusive Zygisk/Module), SuperSU/Superuser, KingRoot/KingUser, BusyBox, Root Checker oder Xposed/LSPosed. Solche Funde sind in der Regel kein »Zufall«, wenn du Root nie eingerichtet hast. Als zusätzlicher Plausibilitätscheck schaust du in die

Entwickleroptionen

, ob dort »USB-Debugging« oder »OEM-Entsperrung« aktiv sind, obwohl du das nie gebraucht hast, und ob Apps plötzlich mit Hinweisen wie »Gerät verändert« reagieren (bspw. Banking-/Bezahl-Apps) oder der Play Store das Gerät als »nicht zertifiziert« einstuft. Ein einzelner Punkt kann noch harmlos sein, aber wenn mehrere Hinweise zusammenkommen und du die Modifikation nicht selbst verursacht hast, ist die pragmatische Konsequenz meist: In so einer Lage ist der Werksreset meist die vernünftigste Abkürzung zurück zu einem vertrauenswürdigen Zustand. Sonst rutscht man sehr schnell in eine aufwendige Spurensuche, die ohne forensisches Know-how kaum sauber zu leisten ist.

¹ SU/Superuser: »su«-Binary, SuperSU, Superuser, One-Click-Root: KingRoot, KingUser, BusyBox (bspw. »BusyBox Free«, »BusyBox Pro«), Root Checker (diverse Apps mit genau diesem Namen), Xposed/LSPosed/EdXposed und Modding-/Flash-Tools: »ROM Manager«, »Flashify«

Schritt 2: Geräteadministratoren kontrollieren

Viele Überwachungs-Apps versuchen sich als »Geräteadministrator« einzutragen. Das ist eine spezielle Rolle, mit der eine App mehr Kontrolle bekommt – und vor allem: Solange diese Rolle aktiv ist, lässt Android die App in der Regel nicht einfach deinstallieren. Du musst sie zuerst als Geräteadministrator deaktivieren und kannst sie erst danach normal entfernen.

Wo du das findest, ist je nach Hersteller und Android-Version unterschiedlich. Am einfachsten ist meist die Suche in den Einstellungen: Tippe oben in die Suchleiste und gib

Geräteadministrator

ein. Der Menüpunkt heißt dann oft »Geräteadministrator«, »Apps zur Geräteverwaltung« oder ähnlich. In einem normalen Privatgerät stehen dort normalerweise keine oder nur wenige, bekannte Einträge. Alles, was du nicht zuordnen kannst, deaktivierst du – und gehst anschließend in die App-Liste, um die betreffende App zu deinstallieren.

Schritt 3: Bedienungshilfen prüfen

Dieser Punkt wird in der Praxis häufig übersehen:

Bedienungshilfen

(Accessibility). Mit diesen Rechten kann eine App Bildschirminhalte mitlesen, Eingaben abgreifen und Abläufe automatisieren. Genau das ist für Spyware praktisch. Öffne die

Bedienungshilfen

über die Einstellungen und prüfe, welche Dienste/Apps aktiv sind. Alles Unbekannte oder Unplausible wird deaktiviert. Wenn dort ein »Service«, »Update« oder ähnlich generischer Eintrag aktiv ist, den du nie bewusst eingeschaltet hast, ist das ein sehr starkes Warnsignal.

Schritt 4: Spezialzugriffe prüfen: Benachrichtigungen, VPN und Nutzungsdaten

Nach Geräteadministratoren und Bedienungshilfen kommen die Spezialzugriffe. Das sind Sonderrechte, die oft mehr verraten als normale Berechtigungen. Du findest sie meist unter

Einstellungen -> Apps -> Allgemein -> Spezieller App-Zugriff

. Am schnellsten geht’s über die Suche nach »Spezieller App-Zugriff«.

Wichtig sind vor allem: »Benachrichtigungszugriff« (liest Messenger-Vorschauen/Einmalcodes), »Nutzungsdatenzugriff« (sieht, welche Apps du wann nutzt), »VPN«/»VPN-Apps« (kann den gesamten Datenverkehr umleiten) sowie Rechte für dauerhaften Hintergrundbetrieb. Im Verdachtsfall entziehst du diese Sonderrechte konsequent allem, was du nicht eindeutig zuordnen kannst. Wenn danach etwas nicht mehr funktioniert, kannst du es später gezielt wieder freigeben.

Schritt 5: Fremdquellen-Installation dichtmachen und prüfen, wer installieren darf

Überwachungs-Apps landen meist nicht über den Play Store auf dem Gerät, sondern werden als APK aus Fremdquellen installiert. Damit das klappt, muss die Installation solcher Apps erlaubt sein. Bei aktuellen Android-Versionen gibt es dafür keinen zentralen Schalter mehr, sondern eine Erlaubnis pro App: Du gestattest zum Beispiel dem Browser, dem Dateimanager oder einer Cloud-App, »unbekannte Apps zu installieren«. In einem normalen Setup ist das bei keiner App dauerhaft aktiv – außer du nutzt bewusst

F-Droid

oder einen anderen vertrauenswürdigen Dritt-Store. Findest du dort erlaubte Installer, die du nicht selbst eingerichtet hast, passt das sehr gut zum Muster: Jemand hatte kurz Zugriff auf das Gerät und hat genau darüber eine App nachinstalliert.

Schritt 6: App-Liste strukturiert prüfen

Erst jetzt lohnt die klassische App-Sichtung. Öffne die App-Liste in den Einstellungen und arbeite sie strukturiert durch. Wenn dein Gerät eine Sortierung nach »zuletzt installiert« oder »zuletzt verwendet« anbietet, nutze sie – falls nicht, geh die Liste einfach manuell durch. Du kannst dir dabei mit der Suchleiste oben helfen: Tippe dort nacheinander typische Tarnwörter ein, um die Liste zu filtern, zum Beispiel »update«, »service«, »system«, »manager«, »device«, »support« oder »sync«. So fallen Einträge schneller auf, die sich hinter sehr allgemeinen Namen verstecken.

Öffne jeden Kandidaten, den du nicht eindeutig zuordnen kannst, und bewerte das Gesamtbild statt nur den Namen: Welche Berechtigungen hat die App, welche Spezialzugriffe, läuft sie im Hintergrund, und passt das zum angeblichen Zweck? Eine harmlose App kann übergriffig sein, aber Spyware fällt oft dadurch auf, dass sie in unplausiblen Bereichen mitmischt: SMS, Kontakte, Standort (vor allem dauerhaft), Mikrofon, Kamera, Benachrichtigungszugriff oder Bedienungshilfen.

Schritt 7: Deinstallation richtig durchführen

Wenn du etwas Verdächtiges entfernst, mach es in der richtigen Reihenfolge. Zuerst Adminrechte weg, dann Bedienungshilfen aus, dann Spezialzugriffe entziehen, erst danach deinstallieren. Viele Apps verweigern die Entfernung genau so lange, wie sie noch irgendwo ein Privileg behalten. Nach der Deinstallation lohnt ein Neustart, damit keine Reste weiterlaufen und du schnell merkst, ob sich etwas erneut einschaltet.

Schritt 8: Schutzfunktionen prüfen

Play Protect

und ähnliche Basisschutz-Funktionen sind bei Weitem nicht unfehlbar, aber sie liefern Hinweise. Wenn Scans deaktiviert sind, die letzte Prüfung ungewöhnlich weit zurückliegt oder sich Einstellungen ohne deinen Grund verändert haben, ist das auffällig. Prüfen kannst du das direkt im Play Store: Öffne den Play Store, tippe oben rechts auf dein Profilbild und wähle »Play Protect«. Dort siehst du, ob die Prüfung aktiv ist und wann zuletzt gescannt wurde. Bei Bedarf kannst du den Scan sofort manuell starten (»Scannen« bzw. Aktualisieren-Symbol) und über das Zahnrad die Schalter kontrollieren, ob die App-Prüfung grundsätzlich eingeschaltet ist. Ein manueller Scan kann helfen, ersetzt aber nicht die Rechteprüfung an den entscheidenden Stellen (Adminrechte, Bedienungshilfen, Spezialzugriffe). Wenn Schutzfunktionen ohne nachvollziehbaren Grund aus sind, ist das ein Warnsignal, nicht nur eine »Einstellungssache«.

Hinweis

Auf googlefreien Geräten (ohne Google Play-Dienste/Play Store) gibt es Play Protect in der Regel nicht – dort fällt dieser Prüfschritt also weg und du stützt dich umso mehr auf die manuellen Kontrollen und zusätzlich einen Malwarescanner wie

Hypatia

oder

LoveLaceAV

.

Schritt 9: Nach dem Säubern Accounts absichern

Nach einer möglichen Überwachung musst du davon ausgehen, dass Zugänge kompromittiert sein können: Passwörter, Sessions, eingeloggte Geräte. Ändere Passwörter deshalb nicht auf dem möglicherweise betroffenen Smartphone, sondern von einem anderen, sauberen Gerät aus, idealerweise nach einem Reset. Dann prüfst du bei den wichtigsten Diensten die angemeldeten Geräte und Sitzungen, meldest Unbekanntes ab und setzt Sessions zurück. Besonderes Augenmerk verdienen Messenger: »verknüpfte Geräte« (Web/Desktop) sind ein stiller Dauerzugang, der auch dann aktiv bleiben kann, wenn du am Smartphone aufräumst. Im Verdachtsfall alle Verknüpfungen lösen und später nur gezielt neu koppeln.

Schritt 10: Wenn der Verdacht bleibt: Werksreset

Wenn du Root/Manipulation nicht sicher ausschließen kannst, wenn verdächtige Einträge immer wieder auftauchen oder du schlicht kein Vertrauen mehr hast, ist der Werksreset der saubere Schlussstrich. Entscheidend ist das Danach: Richte das Gerät als neues Gerät ein, installiere Apps bewusst neu und spiele kein Komplett-Backup zurück, das Apps und Einstellungen wieder in einem Rutsch einspielt. Komfort ist hier oft der Weg, wie Probleme zurückkommen.

Hinweis

Ein Werksreset löscht in erster Linie deine Nutzerdaten (Apps, App-Daten, Konten, Einstellungen). Das hilft zuverlässig gegen typische Spyware, die »nur« als App installiert wurde. Wenn jedoch das Betriebssystem selbst kompromittiert ist (bspw. manipuliertes System-Image/Firmware) oder Root so tief verankert ist, dass er systemweit überdauert, bringt ein Werksreset allein keine verlässliche Bereinigung. In diesem Fall hilft nur ein vollständiges Neu-Flashen eines vertrauenswürdigen Original-Images aus einer verifizierbaren Quelle und – sofern möglich – das anschließende Sperren des Bootloaders. Ein solcher Verdacht ist allerdings ein Fall für eine professionelle forensische Analyse, weil sich das ohne Spezialwissen und geeignete Tools kaum belastbar bestätigen oder ausschließen lässt.

Fazit

Entscheidend ist die Reihenfolge: Zuerst prüfst du, ob das System noch vertrauenswürdig ist. Anschließend entziehst du Apps die »Sonderrechte«, mit denen sie sich verstecken, überdauern oder weitreichend Daten abgreifen können – also Administratorrechte und Bedienungshilfen. Anschließend prüfst du die Spezialzugriffe wie Benachrichtigungszugriff, Nutzungsdaten und VPN. Erst wenn diese Sonderrechte weg sind, lohnt sich das konsequente Entfernen verdächtiger Apps, weil die Deinstallation dann nicht mehr blockiert wird und im Idealfall keine Reste zurückbleiben. Zum Schluss sicherst du deine Konten ab: Passwörter ändern, Sitzungen beenden, verknüpfte Geräte prüfen – am besten von einem sauberen Gerät aus.

Wer so strukturiert vorgeht, übersieht weniger und erhöht die Chance deutlich, typische Überwachungs-Apps nicht nur zu finden, sondern auch zuverlässig zu entfernen. Und falls am Ende doch ein Werksreset nötig ist, ist das kein Zeichen von Scheitern, sondern der konsequente Schlussstrich: Einmal neu aufsetzen, bewusst neu installieren, kein Komplett-Backup zurückspielen – und damit wieder zu einem Smartphone zurückkehren, dem man im Alltag vertrauen kann.

Unterstütze den Blog mit einem Dauerauftrag!

Unabhängig. Kritisch. Informativ. Praxisnah. Verständlich.

Die Arbeit von kuketz-blog.de wird vollständig durch Spenden unserer Leserschaft finanziert. Sei Teil unserer Community und unterstütze unsere Arbeit mit einer Spende.

Mitmachen ➡

Zusatzkapitel: Prävention bei hohem Threat Model

Wer wirklich im Fokus steht, sollte vor allem die Gelegenheit verhindern. Ein gehärtetes System wie

GrapheneOS

, regelmäßige Updates und eine konsequente Gerätesperre (langes Passwort oder lange Passphrase statt kurzer PIN, kurze Auto-Sperre, kein Smart-Lock) senken das Risiko erheblich. Entscheidend ist der Alltag: Gerät gesperrt lassen, nicht aus der Hand geben, nicht unbeaufsichtigt liegen lassen. Weniger Apps, keine unnötigen Spezialzugriffe und keine Fremdquellen-Installation (außer bewusst kontrolliert) reduzieren die Angriffsfläche zusätzlich.

Über den Autor | Kuketz

In meiner freiberuflichen Tätigkeit als Pentester und Sicherheitsforscher bei

Kuketz IT-Security

überprüfe ich IT-Systeme, Webanwendungen und mobile Apps (Android, iOS) auf Schwachstellen. Als Lehrbeauftragter für IT-Sicherheit an der

DHBW Karlsruhe

sensibilisiere ich Studierende für Sicherheit und Datenschutz. Diese Themen vermittle ich auch in

Workshops, Schulungen

sowie auf Tagungen und Messen für Unternehmen und Fachpublikum. Zudem schreibe ich für die Computerzeitschrift

c’t

und bin in

Medien

wie heise online, Spiegel Online und der Süddeutschen Zeitung vertreten. Der Kuketz-Blog und meine Expertise finden regelmäßig Beachtung in der Fachpresse und darüber hinaus.

Mehr Erfahren ➡

Unterstützen

Die Arbeit von kuketz-blog.de wird zu 100% durch Spenden unserer Leserinnen und Leser finanziert. Werde Teil dieser Community und

unterstütze

auch du unsere Arbeit mit deiner Spende.

Folge dem Blog

Wenn du immer über neue Beiträge informiert bleiben möchtest, gibt es verschiedene Möglichkeiten, dem Blog zu folgen:

Mastodon

RSS

Mail

Bleib aktuell ➡

Ähnliche Beiträge

28. März 2019

Magisk: Bei der Macht von Root – Take back control! Teil3

Root für alle: Mit Magisk verschaffen wir uns Root-Zugriff auf unseren Androiden.

19. Dezember 2023

GrapheneOS: Der Goldstandard unter den Android-ROMs – Custom-ROMs Teil7

Keine Frage: GrapheneOS ist derzeit das sicherste und datenschutzfreundlichste Custom-ROM bzw. Android-System.

2. November 2017

NetGuard Firewall – Android unter Kontrolle Teil4

Mit der No-Root Firewall NetGuard lassen sich Tracking- und Werbeanbieter gezielt filtern.

28. Juni 2017

F-Droid und App-Alternativen – Android unter Kontrolle Teil3

F-Droid ist ein verbraucherfreundlicher Android App-Store, in dem datenschutzfreundliche Apps angeboten werden.

10. September 2023

Klimaschutz mit Datenschutz? Der große Elektroauto-Ladeapp-Test

Manche Ladeapps sind eine Datenschutzkatastrophe. Wir haben 41 Apps getestet und geben Tipps für datensparsames Laden.

Weitere Themen

Android

Apple

Audit

Autonomie

Browser

Cloud

Datenschutz

Datensendeverhalten

Digitalpolitik

DSGVO

Encryption

Firewall

Hacking

Hardening

iOS

KI

Kuketz-Blog

Linux

Messenger

Microsoft

OpenWrt

Passwort

Pentest

Politik

RaspberryPi

Recht

Sicherheitsmaßnahme

Surveillance

TDDDG

Testbericht

Tor

Tracking

UnplugBigTech

Vulnerability

Wearable

WordPress

Diskussion

Ich freue mich auf Deine Beteiligung zum Artikel

Wenn du Anmerkungen, Ergänzungen oder konkrete Fragen zum Beitrag hast, bist du herzlich eingeladen, dich im

offiziellen Forum

zu beteiligen. Dort kannst du dich mit anderen austauschen und den Beitrag ausführlich diskutieren.

zur Diskussion ➡

Abschließender Hinweis

Blog-Beiträge erheben

nicht

den Anspruch auf ständige Aktualität und Richtigkeit wie Lexikoneinträge (z.B. Wikipedia), sondern spiegeln den Informationsstand zum Zeitpunkt der Veröffentlichung wieder, ähnlich wie Zeitungsartikel.

Kritik, Anregungen oder Korrekturvorschläge zu den Beiträgen nehme ich gerne per

E-Mail

entgegen.

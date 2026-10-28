# Turkey: law history

This repository will hold the legislation of Turkey (TR) as a history: one file per provision and one commit per law taking effect, dated by the day it took force, with the law that made each change as the commit author. It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law), which places it at `tr/` in the world tree.

**Status:** no law yet. This first commit records where the law of Turkey can be read and what a build would need.

**Can it be built?** Only current text or the gazette is online, so a history has to be rebuilt by applying each amending act.

**This commit is a placeholder.** The first real build must replace this history from scratch and force-push. It must never append law commits on top of it: they are dated by when each law took effect, often decades earlier, so dates in `main` would run backwards and break every on-date lookup. Builders should refuse to append when the root commit is this placeholder (its subject ends "sources, before any law").

**Official sources**

- [Mevzuat](https://www.mevzuat.gov.tr): Current text with inline notes such as “(Değişik: 2/7/2012-6352/1 md.)” naming each amending law.

**Notes for a build from PDFs** (learned on Malta)

- Letter-spaced, justified PDF lines extract as “w o r d”. Read character boxes (for example PyMuPDF `rawdict`), keep a space only where the gap is over 0.5 pt, and treat differences in whitespace alone as no change.
- One address can serve a wrong-language or duplicate upload (212 of 5,079 in Malta). Detect the language from the text and keep one version per date.

**Existing open projects to check first**

- [acik-mevzuat](https://github.com/onurcan-b/acik-mevzuat): Versionable JSON and Markdown legislation.

These are volunteer projects. Reconcile any of them against the official text before relying on it: a transcription is not the law (c3e/grundgesetz, for example, differs from the official gazette in 43 article texts on 20 July 2017).

All sources, with their status, are in [SOURCES.md](SOURCES.md). How these files were made is in [REPRODUCE.md](REPRODUCE.md).

This repository describes sources; it is not legal advice and holds no legal text yet.

# Docker and UI Audit

Date: 2026-04-27

## Verification Run

- `python -m pytest` from `backend`: 5 passed.
- `npm run build` from `frontend`: passed.
- `npm audit --omit=dev` from `frontend`: 0 production vulnerabilities.
- `npm audit` from `frontend`: 6 moderate development-tooling vulnerabilities in Angular build dependencies, with no fix currently available from npm audit.
- `docker --version`: failed because Docker is not installed or not available in `PATH`; container build/run was not executable on this machine.

## Audit Health Score

| # | Dimension | Score | Key Finding |
|---|-----------|-------|-------------|
| 1 | Accessibility | 2 | Textarea removes focus outline and status text is not announced to assistive tech. |
| 2 | Performance | 3 | Angular bundle is small; preview rendering is simple but runs on each Markdown signal update. |
| 3 | Responsive Design | 3 | Mobile stacks correctly, but several touch targets are below 44px. |
| 4 | Theming | 3 | CSS tokens exist, but some colors remain hard-coded and there is no dark/high-contrast mode. |
| 5 | Anti-Patterns | 4 | No obvious generic AI dashboard patterns, gradient text, or decorative card grid. |
| **Total** | | **15/20** | **Good** |

## Anti-Patterns Verdict

Pass. The UI reads as a restrained local editor rather than a generic AI-generated SaaS dashboard. It avoids decorative gradients, metric cards, glass effects, nested cards, and oversized hero content. The main tell is the default `Inter` font stack in `frontend/src/styles.css:21`; it is conventional rather than distinctive, but acceptable for a utility-first local tool.

## Detailed Findings

### [P1] Focus Indicator Removed From Editor

- Location: `frontend/src/styles.css:184`
- Category: Accessibility
- Impact: Keyboard users may not be able to see when the Markdown editor has focus.
- WCAG/Standard: WCAG 2.4.7 Focus Visible
- Recommendation: Add a visible `textarea:focus-visible` outline or focus ring instead of removing outline without replacement.

### [P2] Touch Targets Are Smaller Than 44px

- Location: `frontend/src/styles.css:31`, `frontend/src/styles.css:77`
- Category: Responsive
- Impact: Buttons and the brand mark are usable on desktop, but mobile touch accuracy is less forgiving.
- WCAG/Standard: WCAG 2.5.5 Target Size (Enhanced)
- Recommendation: Raise interactive `min-height` to at least 44px on touch layouts.

### [P2] Status Updates Are Not Announced

- Location: `frontend/src/app/app.component.html:34`
- Category: Accessibility
- Impact: Screen reader users may not hear sync/save outcomes.
- WCAG/Standard: WCAG 4.1.3 Status Messages
- Recommendation: Add `role="status"` and `aria-live="polite"` to the status element.

### [P2] API Base URL Is Compile-Time Hard-Coded

- Location: `frontend/src/app/api.service.ts:22`
- Category: Operations / Portability
- Impact: Works for local Docker and local dev, but makes reverse proxy or alternate host deployments require a rebuild.
- Recommendation: Use an Angular environment file or a runtime-served config file for `API_BASE_URL`.

### [P2] Docker Build Not Verified Locally

- Location: Docker environment
- Category: Operations
- Impact: Dockerfiles and Compose are present, but the image build was not proven on this machine because `docker` is unavailable.
- Recommendation: After installing Docker Desktop, run `docker compose build` and `docker compose up`.

### [P3] Development Toolchain Has Moderate Audit Warnings

- Location: `frontend/package-lock.json`
- Category: Supply Chain
- Impact: Production dependency audit is clean. The remaining warnings are in dev tooling (`postcss`, `webpack-dev-server`, `sockjs`, `uuid`) and currently have no npm audit fix.
- Recommendation: Re-run `npm audit` after Angular releases patched build tooling.

### [P3] Theme Tokens Are Partial

- Location: `frontend/src/styles.css:3-10`, `frontend/src/styles.css:28`, `frontend/src/styles.css:122`, `frontend/src/styles.css:179`
- Category: Theming
- Impact: The palette is mostly tokenized, but hard-coded values make future theme work less consistent.
- Recommendation: Move remaining hard-coded colors into variables and consider OKLCH tokens for predictable contrast scaling.

## Positive Findings

- Docker Compose keeps Notion credentials in `.env` and does not bake them into images.
- Compose binds frontend and backend ports to `127.0.0.1`, matching the local-only security model.
- Backend container runs as a non-root user and has a healthcheck.
- Frontend runtime uses an unprivileged Nginx image.
- Production frontend audit reports zero vulnerabilities.
- The UI structure uses real landmarks (`main`, `aside`, `nav`, `header`) and native buttons.

## Recommended Actions

1. **[P1] `/polish`** - Restore visible focus styles for the Markdown editor and interactive elements.
2. **[P2] `/adapt`** - Increase touch target sizing and refine the mobile stacked editor layout.
3. **[P2] `/harden`** - Move frontend API URL to runtime configuration and add screen-reader status announcements.
4. **[P2] `/audit`** - Re-run after Docker Desktop is installed and `docker compose build/up` can be verified.
5. **[P3] `/polish`** - Tokenize remaining hard-coded colors and revisit typography.

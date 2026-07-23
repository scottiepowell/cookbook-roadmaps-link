# 0033E Website Marketing And Community Outreach ADR

## Goal

Investigate marketing approaches for the Cookbook AI website, including the idea of using cooking-video transcripts to create thoughtful, curated, AI-assisted comment drafts that could promote the site to people reading comments.

This is an ADR/research task only. Do not implement marketing automation, comment posting, transcript scraping, or platform integrations in this task.

## Context

The product owner wants to explore website marketing. One proposed idea is to analyze transcripts from popular cooking channels on YouTube and draft thoughtful comments that mention or promote the website.

This must be handled carefully. The ADR must distinguish policy-compliant, human-reviewed community engagement from spam, bot activity, undisclosed promotion, scraping, or platform-policy violations.

## Required Work

Create:

```text
docs/website-marketing-community-outreach-adr.md
```

The ADR should cover:

- marketing goals and target audiences;
- acceptable marketing channels;
- YouTube/community comment idea as an exploration only;
- policy, copyright, spam, disclosure, and reputational risks;
- requirement for human review and authentic participation;
- prohibition on automated posting, mass commenting, fake engagement, or undisclosed AI-driven promotion;
- transcript sourcing rules and copyright/terms review requirements;
- comment quality standards: thoughtful, relevant, non-deceptive, non-repetitive, and not impersonating users;
- alternatives such as blog content, recipe landing pages, SEO, newsletter, partnerships, creator outreach, and affiliate/partner content;
- metrics for marketing experiments;
- safe experiment design;
- go/no-go criteria;
- explicit non-goals.

If internet access is available, research current high-level platform policy and marketing/legal considerations. If internet access is not available, state the limitation and keep the ADR conceptual.

Update as appropriate:

```text
README.md
docs/ai-feature-status.md
docs/ai-implementation-backlog.md
docs/product-priority-roadmap-after-0032A.md
```

Create:

```text
outbox/0033E-marketing-website-community-outreach-adr-results.md
```

## Acceptance Criteria

- ADR exists.
- ADR evaluates the YouTube/transcript/comment idea without implementing it.
- ADR explicitly rejects spam, bot posting, fake engagement, undisclosed promotion, and automated mass commenting.
- ADR requires human review and policy/compliance checks before any external outreach.
- ADR identifies safer marketing alternatives.
- No scraper, browser automation, API client, comment poster, transcript downloader, account automation, or marketing integration is added.
- No screenshots, traces, secrets, prompts, provider outputs, transcripts, or generated marketing comments are committed.

## Validation

Run:

```powershell
cd C:\Users\scott\cookbook-roadmaps-link
git diff --check
& "C:\Program Files\Git\bin\bash.exe" scripts\validate-repo.sh
```

## Commit

```bash
git add docs README.md outbox/0033E-marketing-website-community-outreach-adr-results.md
git commit -m "docs: add website marketing outreach adr"
git pull --rebase origin main
git push origin main
```

# Production Handoff Strategy

This document defines a clean, repeatable release flow for Joulaa.

## Branch Model

- `v2-agent-platform`: Active development branch for new features.
- `release/v1.0.0`: Stabilization branch for the current production candidate.
- `production`: Branch that mirrors what is deployed to production.
- `main`: Reserved as long-term default branch (can be aligned later once production flow is fully adopted).

## Release Rules

1. New features land in `v2-agent-platform`.
2. When preparing a release, cut a release branch from `v2-agent-platform`.
3. Only release-safe changes are allowed in `release/*`:
   - bug fixes
   - config fixes
   - docs/runbook updates
4. When approved, merge/cherry-pick release commits into `production`.
5. Tag `production` with a semantic version tag (`v1.0.0`, `v1.0.1`, ...).
6. Hotfixes go to `production` first, then are back-merged to `v2-agent-platform`.

## Versioning

- Use SemVer:
  - Major: breaking changes
  - Minor: new backward-compatible features
  - Patch: fixes only

Recommended initial tag sequence:
- `v1.0.0-rc.1` on release candidate
- `v1.0.0` once production deploy is validated

## Production Handoff Checklist

Before first production deploy:

1. API smoke tests pass on release branch.
2. Registration/login flow tested from frontend.
3. Required env vars set in production secrets:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `REDIS_URL`
   - mail/AI keys as needed
4. Database migration plan verified (`alembic upgrade head`).
5. Rollback plan documented (previous image/tag + DB rollback constraints).
6. Monitoring and error tracking enabled.
7. Deploy approved by product + engineering owners.

## Command Playbook

Create release branch:

```bash
git checkout v2-agent-platform
git pull
git checkout -b release/v1.0.0
git push -u origin release/v1.0.0
```

Promote to production:

```bash
git checkout production
git merge --no-ff release/v1.0.0
git tag -a v1.0.0 -m "Joulaa production release v1.0.0"
git push origin production --tags
```

Hotfix flow:

```bash
git checkout production
git checkout -b hotfix/v1.0.1
# apply fix
git commit -m "fix: ..."
git checkout production
git merge --no-ff hotfix/v1.0.1
git tag -a v1.0.1 -m "Joulaa hotfix v1.0.1"
git push origin production --tags

git checkout v2-agent-platform
git merge --no-ff hotfix/v1.0.1
git push origin v2-agent-platform
```

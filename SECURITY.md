# Security notes

## The committed signing key

Earlier revisions of this repository contained a working `SECRET_KEY` in
`.env.example`. Anyone with a copy of the repository could mint a valid token for
any account, including an administrator, without ever contacting the server.

What was done:

- The key is gone from every example file.
- `SECRET_KEY` now has **no default**. The application will not start without one.
- `app/config.py` rejects that specific key by value, so it cannot be pasted back
  in by habit or by copying an old `.env`.
- Every token signed with it is worthless once a new key is generated, because
  signature verification fails.

If this repository was ever pushed anywhere public, treat the old key as
permanently compromised. Generate a new one and never commit it:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Rotating `SECRET_KEY` invalidates all existing sessions. Everyone signs in again.
That is the intended effect.

## Reporting a problem

Report suspected vulnerabilities privately to the project maintainer rather than
opening a public issue. Include the request id from the error response if you have
one; it maps directly to a line in the server log.

## What the application does and does not defend against

Handled:

- Password storage with bcrypt at a configurable work factor (minimum 12 in
  production, enforced at startup).
- Authorisation checked server-side on every endpoint, with a test matrix covering
  each role against each route.
- Role escalation closed off: self-registration cannot set a role, and there is no
  unauthenticated login path of any kind.
- Attachment links restricted to `https`, with loopback and private hosts rejected,
  so a pasted link cannot become script execution or an internal network probe.
- Rate limiting on sign-in, registration and write endpoints.
- Contact details released only to the staff member actually assigned to an issue.
- Errors returned as a fixed shape with a request id, never a stack trace.

Not handled, and deliberately out of scope for this version:

- The rate limiter holds counters in process memory. Behind more than one worker
  the effective limit multiplies by the worker count. Move the counters to a shared
  store before scaling out.
- No account lockout after repeated failures, only rate limiting.
- No email verification of college addresses, and no password reset flow. An
  administrator resets a password by creating or updating the account.
- No audit log export. The timeline records who did what to an issue, but
  administrative changes to routing rules are recorded only in application logs.
- File uploads are not accepted at all; evidence is a link to a file hosted
  elsewhere. That removes an entire class of upload vulnerabilities and adds a
  dependency on whatever service hosts the link.

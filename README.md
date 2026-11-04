# Quiz App (Flet + Supabase)

A Python/Flet quiz application with Supabase authentication, quiz attempts, results, profiles, premium status, and admin screens.

## Project layout

- `main.py` — app startup and page navigation.
- `pages/` — user-facing screens and quiz flow.
- `admin/` — admin category, quiz, question, and CSV import screens.
- `services/` — Supabase data access and application services.
- `models/` — dataclasses for quiz-domain objects.
- `supabase/quiz_app_initial_migration.sql` — initial database schema and policies.
- `config.py` — local and public-client configuration.
- `build_windows.ps1` — local testing build; copies `.env` into the generated app.
- `build_windows_release.ps1` — public release build; does not copy `.env`.

## Development setup

1. Use the Python version compatible with your installed Flet release.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and fill in your Supabase project URL and publishable/anon key.
5. Run the app:

   ```powershell
   python main.py
   ```

`.env` is intentionally ignored by Git. Do not commit real environment files.

## Build for local Windows testing

Run this from the project root in PowerShell:

```powershell
.\build_windows.ps1
```

This copies `.env` to `build\windows\app\.env`, matching the packaged app's runtime lookup. It is for local testing only. Do not distribute a build containing `.env`.

## Build a public Windows release

1. In `config.py`, set `PUBLIC_SUPABASE_URL` and `PUBLIC_SUPABASE_KEY`.
2. Use only the Supabase publishable key or legacy `anon` key. **Never** use a service-role or secret key in a desktop app.
3. Verify that Row Level Security (RLS) and table policies prevent unauthorized reads/writes.
4. Run:

   ```powershell
   .\build_windows_release.ps1
   ```

5. Test the output on a clean Windows account or computer.

A publishable/anon key is designed for client use, but it is not an authorization system. Database policies and backend checks must enforce permissions. Keep `.env` out of public artifacts.

## Important release security review

**Do not publish the current Premium flow as a paid feature yet.** The existing `PremiumPage` calls the `activate_subscription` RPC directly, and the SQL function in the current migration permits a signed-in user to activate their own subscription. There is no payment verification in that flow. Before offering paid Premium access, replace this with a trusted server-side payment verification process (for example, a Supabase Edge Function that validates payment-provider webhooks or verified purchase receipts).

Also review the policies and authorization for profiles, quiz attempts, device associations, questions, admin operations, and CSV import before public release.

## Dependency note

`requirements.txt` has been normalized to UTF-8 for tooling compatibility. Its pinned package versions were retained to avoid introducing an untested dependency upgrade during this refactor.

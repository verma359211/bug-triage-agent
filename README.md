# Bug Triage Agent

A CLI walking skeleton that investigates a reported defect in a Git repository and, for backend reports, asks GitHub Actions to run a generated reproduction test.

The implementation will be added milestone by milestone. Ground-truth evaluation cases live in `eval/bugs.json` and must never be copied into the target repository.

## M2 sandbox check

After copying `.env.example` to `.env` and filling in its values:

```bash
python -m pip install -r requirements.txt
python eval/run_sandbox_check.py
```

The check sends three sample Jest tests through GitHub Actions three times each and prints expected versus actual classifications.

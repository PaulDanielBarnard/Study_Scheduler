# Contributing

Thanks for your interest in improving Study Scheduler! A few guidelines to make contributions smooth.

1. Fork the repository and create a topic branch for your work (feature/bugfix/docs).
2. Keep changes small and focused. Add tests for new behavior when possible.
3. Run the test suite locally before opening a PR:

```powershell
cd Study_Scheduler
python -m pip install --upgrade pip
pip install -r requirements.txt
pytest -q
```

4. Follow standard commit message style and include a clear PR description explaining the reason for the change and the testing performed.
5. If your change touches the UI, include screenshots or short notes about the user-visible changes.

Maintainers will review and request changes if necessary. Thanks!

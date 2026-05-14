# Publish To GitHub — Safe Commands

These commands prepare and push the repository to GitHub. They require the `gh` CLI (recommended) or standard `git` remote steps. Run locally; do not run without your GitHub authentication.

1) Create repository (using `gh`):

```bash
gh repo create your-username/nebula-interface --public --source . --remote origin --push
```

2) Create annotated tag and push:

```bash
git tag -a v1.0 -m "Nebula Interface v1.0"
git push origin v1.0
```

3) Enable GitHub Pages (if using docs):

```bash
# Use repo settings UI or:
gh api repos/:owner/:repo/pages -X PUT -f source.branch=master -f source.path="/"
```

4) Add CI secrets (if needed):

```bash
gh secret set MQTT_BROKER --body "mqtt.example.com"
gh secret set MQTT_USERNAME --body "your_user"
gh secret set MQTT_PASSWORD --body "your_pass"
```

Notes
-----
- If you prefer manual git workflow instead of `gh`, create the remote on GitHub and run `git remote add origin <url>` then `git push -u origin master`.
- I will not run these commands without your explicit approval and credentials.

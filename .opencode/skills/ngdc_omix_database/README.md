# NGDC OMIX data-access agent skill

This is a reusable agent-style `SKILL.md` folder with Python scripts for **public accession metadata retrieval**, **published open-access file downloads**, **controlled-access application drafting**, and **post-approval FTP retrieval**.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/omix.py record OMIX007792 --output record.json
python scripts/omix.py download OMIX007792 --file-id OMIX007792-03 --dry-run
python scripts/omix.py download OMIX007792 --file-id OMIX007792-03 --dir data
python scripts/omix.py request-draft OMIX010131 --output request.md

python -m unittest discover -s tests -v
```

For approved controlled data only:

```bash
export NGDC_USERNAME='your-login'
python scripts/approved_ftp.py --list-dir '/path-provided-after-approval'
python scripts/approved_ftp.py --remote-file '/approved/path/filename.ext' --dir authorized
```

The scripts are **not** a documented OMIX API client, and they don't bypass access controls. Read `SKILL.md` and `references/omix-access.md` for setup, limitations, security and official documentation links. Script dependencies are small; the FTP helper uses Python's standard library.

**Verification caveat:** Code is syntax- and fixture-tested offline. Live NGDC network calls were not executed in the build environment; results depend on the site remaining accessible and its HTML structure remaining compatible.

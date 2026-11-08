# NGDC OMIX: access reference

Last checked against public NGDC pages: **2026-11-08**. These URLs and policy descriptions come from the NGDC/CNCB site and may change.

## Canonical links

| Resource | Authoritative URL | What it covers |
|---|---|---|
| OMIX home | https://ngdc.cncb.ac.cn/omix/ | Archive description, support, citations |
| Released data browser | https://ngdc.cncb.ac.cn/omix/releaseList | Website-based catalog and search |
| Accession page | https://ngdc.cncb.ac.cn/omix/release/OMIX007792 | Summary, access type, file table, HTTPS/FTP buttons |
| OMIX help | https://ngdc.cncb.ac.cn/omix/docs | Official policy and download links |
| 2025 English user guide (PDF) | https://ngdc.cncb.ac.cn/omix/download-guide/Submission-Guidance-FAQ-OMIX-EN.pdf | Public HTTP and FTP download steps; see pp. 29 onward |
| Human genetic data access policy | https://ngdc.cncb.ac.cn/omix/term_and_policy?lang=en_GB | Open vs controlled; obligations |
| Controlled data FTP guidance | https://ngdc.cncb.ac.cn/omix/request-download?lang=en_GB | `omix.big.ac.cn:21`; passive FTP; NGDC login; time-limited |
| NGDC help email | mailto:gsa@cncb.ac.cn | Questions about access or broken download links |

## Access decision table

| Record state | Allowed workflow | Not allowed |
|---|---|---|
| Open-access and released; valid HTTPS link | Download only published file links, subject to archive use terms | Guess private URLs or ignore access terms |
| Controlled-access | Apply to data submitter / custodian and await approval | Scrape protected files or bypass login |
| Controlled-access with project-specific instructions | Use its named approval portal (example below) | Assume a single generic OMIX application endpoint |
| Unavailable / MOST-registration restriction | Report restriction; contact custodian/support | Treat the existence of a file row as download permission |
| Not released or unknown | Verify through the OMIX page / portal | Assume open access |

## Officially documented download methods

**Public HTTPS:** The `Files & Download` section of each open-access record shows per-file `HTTPs` links. Copy or use these exact URLs. Record metadata includes `File ID`, `File Title`, sample count, file type, size and suffix. Some links may fail due to migration, permissions, or temporary service issues; a visibly listed HTTPS link is not a guarantee of live transfer.

**Public FTP:** The English user guide recommends a dedicated FTP client for large transfers. It describes right-clicking `FTP Download` -> Copy Link Address (example `ftp://download.cncb.ac.cn/OMIX/OMIX006457/`) and opening it in FileZilla. Do not confuse this *public* FTP host with the *approved controlled-data* host.

**Approved controlled FTP:** After approval, NGDC's dedicated guide specifies host **`omix.big.ac.cn`**, port **`21`**, NGDC username/password and **passive** FTP. The folder is accessible only within the granted download window. The server's encryption capabilities are not confirmed; FTP without TLS can expose credentials. Use FTPS if supported, or consult institutional security guidance.

**Downloads subject to regulation:** An OMIX record can say data cannot be downloaded because it has not been registered in the Human Genetic Resource Management Platform of MOST. The presence of visible metadata doesn't override this restriction.

## Application flow (human review required)

1. Identify the record and its `Data Accessibility` value.
2. Check for a record-specific request link. For example, controlled-access `OMIX010131` explicitly directs applicants to the Aging BioBank website: https://cbb.cncb.ac.cn/abb/ . Other datasets may have different custodians.
3. Prepare scientific aims, team, PI, requested files, institutional affiliation, ethics protocol and storage plan. Consult `access-request-template.md`.
4. Apply via the official route, let the data custodian review it, sign agreements if required.
5. Download **only after approval**, from the explicitly granted links or paths before access expires.

**Principle for the Access of Human Genetic Resource Data in NGDC:** the submitter decides whether to authorize access; use must follow the approved research scope, avoid onward sharing and individual identification, and comply with security responsibilities. Cite accession numbers for datasets used in research results.

## Discoverability and API limitations

OMIX is searchable through its released-data browser and broader NGDC search portals. **No verified supported public OMIX REST API contract is provided in the documentation examined here.** `scripts/omix.py` is a web page reader, not a claim that OMIX offers JSON APIs. Avoid automated site-wide enumeration or constructing undocumented endpoints. If the public page is JavaScript-only, has layout changes, or requires interactive checks, use the browser.

## Licensing, ethics and citation

The OMIX help page states that OMIX is **free for academic use only** and commercial use requires licensing contact. Additional data-specific and legal conditions may apply even to publicly downloadable human data. Avoid uploading any sensitive controlled data to unrelated cloud services or exposing it in a public repository.

Cite the source accession (e.g., `OMIX007792`) with the NGDC OMIX record URL and relevant study. The official home page recommends references including:

- *The GSA Family in 2025: A Broadened Sharing Platform for Multi-Omics and Multimodal Data*; DOI https://doi.org/10.1093/gpbjnl/qzaf072
- *Database Resources of the National Genomics Data Center, China National Center for Bioinformation in 2025*; DOI https://doi.org/10.1093/nar/gkae978

## Troubleshooting

- **Page couldn't be parsed:** check the accession record in a normal browser. Website markup may have changed; never invent links.
- **403, 404 or HTML returned for a data link:** inspect the download button on the published record and retry later or contact NGDC. Do not assume a listed link actually works.
- **Controlled file, no public link:** apply for access, do not try guessing paths.
- **FTP over TLS fails:** the approved server may not support TLS. Use FileZilla as NGDC documents; avoid plain FTP credentials unless institutional policies permit and user explicitly accepts risk.
- **FTP directory not found:** use the directory supplied in the approval notice, verify that the approval window has not expired and confirm credentials; don't brute-force directory names.
- **Too big:** use the file size metadata to plan storage and budget. The public downloader defaults to 1 GB per file unless `--max-size-gb` is increased.
- **Transfer interrupted:** `.part` supports HTTP Range resume when the server honors it. Check the resulting local SHA-256 and, when available, compare with an independent publisher-provided hash.

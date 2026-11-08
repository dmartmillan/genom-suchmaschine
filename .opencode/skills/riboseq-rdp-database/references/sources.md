# Verified sources

Primary sources for the skill (accessed 2026-11-08):

1. RDP portal: https://rdp.ucc.ie/home — main portal. Direct access was blocked with HTTP 403 from the inspection environment; live endpoint testing was not possible.
2. RiboSeq.Org official portal overview: https://riboseq.org/tutorials/RDP_Overview.html — homepage, Samples/Studies filters, metadata export, Generate Links, Options, Links page.
3. RiboSeq.Org bulk download tutorial: https://riboseq.org/tutorials/RDP_download_all.html — browser-generated bulk download Bash script.
4. RDP-Tools official docs: https://rdp-tools.readthedocs.io/en/latest/ — install, `database sample-fields`, `database samples --query`, `--fields`, `--limit`, inflate/collapse.
5. RDP-Tools source: https://github.com/riboseqorg/RDP-Tools — upstream utility repository.
6. Data Portal source: https://github.com/riboseqorg/RiboSeqOrg-DataPortal — server source (REST paths must be checked against the current deployment).
7. RDP-MCP project: https://pypi.org/project/RDP-MCP/ — published alternative MCP tooling, including `query_samples`, `get_sample_details`, and `get_file_links`.
8. Tierney et al., "RiboSeq.Org: an integrated suite of resources for ribosome profiling data analysis and visualization," Nucleic Acids Research 53(D1), D268–D274 (2025), DOI: https://doi.org/10.1093/nar/gkae1020 — architecture, public accessibility and REST API description.

# Bibliography verification

Checked against primary arXiv records on 29 July 2026.

| Key | arXiv | Status |
|---|---|---|
| `camel` | 2503.18813v2 | verified |
| `designpatterns` | 2506.08837v3 | verified |
| `agentdojo` | 2406.13352v3 | verified |
| `progent` | 2504.11703v3 | verified |
| `pact` | 2605.11039v1 | verified; recent work |
| `forge` | 2602.16708v3 | verified; recent work |
| `struq` | 2402.06363v2 | verified |
| `spotlighting` | 2403.14720v1 | verified |

## Classical security literature (Priority A)

Source: `reports/analysis/2026-08-13-foundational-security-literature.md` §29.
Metadata checked against Google Scholar, publisher records, or DOIs on
30 August 2026. Structured findings, limitations, and novelty-impact
assessments are recorded in
`research/reports/analysis/literature_corpus.json`. The verification
protocol is documented in
[docs/research/LITERATURE_VERIFICATION_PROTOCOL.md](../../../docs/research/LITERATURE_VERIFICATION_PROTOCOL.md).

| Key | Citation | Status |
|---|---|---|
| `biba1977` | Biba, K. J. (1977). *Integrity Considerations for Secure Computer Systems*. MITRE Technical Report MTR-3153. Also distributed as ESD-TR-76-372. | Scholar verified; abstract and key sections read |
| `lomac` | Fraser, T. (2000). LOMAC: Low-Water-Mark Integrity Protection for COTS Environments. *Proceedings of the 2000 IEEE Symposium on Security and Privacy*, 230–245. DOI: 10.1109/SECPRI.2000.848460. | Scholar verified; abstract and key sections read |
| `denning1976` | Denning, D. E. (1976). A Lattice Model of Secure Information Flow. *Communications of the ACM*, 19(5), 236–243. DOI: 10.1145/360051.360056. | DOI verified; abstract and key sections read |
| `sabelfeld2003` | Sabelfeld, A. & Myers, A. C. (2003). Language-Based Information-Flow Security. *IEEE Journal on Selected Areas in Communications*, 21(1), 5–19. DOI: 10.1109/JSAC.2002.806121. | DOI verified; abstract and key sections read |
| `myersliskov` | Myers, A. C. & Liskov, B. (2000). Protecting Privacy Using the Decentralized Label Model. *ACM Transactions on Software Engineering and Methodology*, 9(4), 410–442. DOI: 10.1145/363516.363524. | Scholar verified; abstract and key sections read |
| `declassification-survey` | Sabelfeld, A. & Sands, D. (2009). Dimensions and Principles of Declassification. *Journal of Computer Security*, 17(5), 609–655. | Scholar verified; abstract and key sections read |
| `robust-declassification` | Zdancewic, S. & Myers, A. C. (2001). Robust Declassification. *Proceedings of the 14th IEEE Computer Security Foundations Workshop*, 15–23. | Scholar verified; abstract and key sections read |
| `attacker-control` | Askarov, A. & Myers, A. C. (2007). Attacker Control and Impact for Confidentiality and Integrity. *Logical Methods in Computer Science*, 7(3), 2011 (extended from CSF 2007). arXiv: 1107.5594. | **Primary source verified; full text read from arXiv HTML** |
| `nonmalleable-ifc` | Cecchetti, E., Myers, A. C. & Arden, O. (2017). Nonmalleable Information Flow Control. *Proceedings of the 44th ACM SIGPLAN Symposium on Principles of Programming Languages (POPL)*, 257–270. DOI: 10.1145/3009837.3009843. arXiv: 1708.08596. | **Primary source verified; abstract and key sections read from arXiv** |

"Scholar verified" means title, authors, year, venue, and volume/pages matched
a Google Scholar result or publisher record. "Abstract and key sections read"
means the abstract and sections most relevant to Conflux were inspected; full
text primary-source reading remains an operator action. DOIs were checked
against the DOI resolver; some DOIs for older CSF/CSFW proceedings did not
resolve to the correct paper and are noted in the corpus. Structured
key findings, limitations, and novelty-impact assessments for each entry are
recorded in `research/reports/analysis/literature_corpus.json` and validated
by `tests/test_literature_corpus.py`.

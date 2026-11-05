# Preparing a public release

Author: OD. Optional support: https://nowpayments.io/donation/oktayd

1. Run synthetic tests: `python -m unittest discover -s DNA_Software/Launcher -p "test_*.py"`.
2. Build: `powershell -NoProfile -File DNA_Software/Launcher/build.ps1`.
3. If a publisher certificate is available, Authenticode-sign the final EXE before computing release checksums. No certificate or signing secret is included in this repository. Do not publish private keys.
4. Generate the public source archive with `python DNA_Software/Launcher/public_package.py`.
5. Stage the Windows/source archives, command schemas and checksums with `python DNA_Software/Launcher/release_tools.py`. Output is `DNAWorkbench_Release/<version>` beneath the app root. This does not upload or publish anything.
6. Review notices, scientific limits and clean-PC setup. Set the actual GitHub `release_repository` only after the owner has created the repository. Configure protected release tags, private vulnerability reporting and signing/attestation in CI as appropriate.
7. Publish only the staged artifacts and reviewed allowlisted sources. Never upload the complete SSD/workspace.

The current package is unsigned alpha software. Checksums are not signatures. Native Windows components and WSL still have host requirements. No successful clean-PC installation claim is made solely from synthetic tests.


Support: [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments donation](https://nowpayments.io/donation/oktayd). Optional [NOWPayments registration affiliate link](https://account.nowpayments.io/de/create-account?link_id=2318328728): OD may benefit; no registration is required to use the suite. Supplied QR image belongs to the author-provided support assets.

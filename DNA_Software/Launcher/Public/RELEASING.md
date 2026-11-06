# Preparing a public release

Author: OD. Optional support: https://nowpayments.io/donation/oktayd

1. Run synthetic tests: `python -m unittest discover -s DNA_Software/Launcher -p "test_*.py"`.
2. On Windows, build the EXE with `powershell -NoProfile -File DNA_Software/Launcher/build.ps1`. On Linux, `sh DNA_Software/Launcher/build_linux.sh` writes `DNAWorkbench-Linux-x64.zip`. Linux does not compile the EXE.
3. If a publisher certificate is available, Authenticode-sign the final EXE before computing release checksums. No certificate or signing secret is included in this repository. Do not publish private keys.
4. Generate the public source archive with `python DNA_Software/Launcher/public_package.py`.
5. On Windows, stage `DNAWorkbench-Windows-x64.zip` with `python DNA_Software/Launcher/release_tools.py --target windows`. On Linux, `build_linux.sh` already calls `--target linux`. Output is `DNAWorkbench_Release/<version>` beneath the app root. This does not upload or publish anything. Publish both zips.
6. Review notices, scientific limits and clean-PC setup. Set the actual GitHub `release_repository` only after the owner has created the repository. Configure protected release tags, private vulnerability reporting and signing/attestation in CI as appropriate.
7. Publish only the staged artifacts and reviewed allowlisted sources. Never upload the complete SSD/workspace.

The current package is unsigned alpha software. Checksums are not signatures. Windows, WSL and the Linux desktop each have host requirements. No successful clean-PC installation claim is made solely from synthetic tests.


Support: [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments donation](https://nowpayments.io/donation/oktayd). Optional [NOWPayments registration affiliate link](https://account.nowpayments.io/de/create-account?link_id=2318328728): OD may benefit; no registration is required to use the suite. Supplied QR image belongs to the author-provided support assets.

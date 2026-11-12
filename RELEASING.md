# Preparing a public release

Author: OD. Optional support: https://nowpayments.io/donation/oktayd

1. Run synthetic tests: `python -m unittest discover -s DNA_Software/Launcher -p "test_*.py"`.
2. On Windows, build the EXE with `powershell -NoProfile -File DNA_Software/Launcher/build.ps1`. On Linux, `sh DNA_Software/Launcher/build_linux.sh` writes `DNAWorkbench-Linux-x64.zip`. Linux does not compile the EXE.
3. If a publisher certificate is available, Authenticode-sign the final EXE before computing release checksums. No certificate or signing secret is included in this repository. Do not publish private keys.
4. Generate the public source archive with `python DNA_Software/Launcher/public_package.py`.
5. Stage Windows x64 with `release_tools.py --target windows`. Build the ARM64 launcher with `build.ps1 -Architecture arm64` and stage it with `release_tools.py --target windows --arch arm64`. Linux uses `--target linux` with the host architecture or an explicit `--arch`. Build macOS previews on macOS with Xcode tools using `--target macos --arch x64` or `--arch arm64`.
6. Collect the verified ZIPs and generate one SHA-256 list for the exact files attached to the release. Label preview architectures and describe the verification completed for each.
7. Review notices, scientific limits and clean-PC setup. Set the actual GitHub `release_repository` only after the owner has created the repository. Configure protected release tags, private vulnerability reporting and signing/attestation in CI as appropriate.
8. Publish only the staged artifacts and reviewed allowlisted sources. Never upload the complete SSD/workspace.

The current package is unsigned alpha software. Checksums are not signatures. Windows, WSL and the Linux desktop each have host requirements. No successful clean-PC installation claim is made solely from synthetic tests.


Support: [Buy Me a Coffee](https://buymeacoffee.com/okioki) · [NOWPayments donation](https://nowpayments.io/donation/oktayd). Supplied QR image belongs to the author-provided support assets.

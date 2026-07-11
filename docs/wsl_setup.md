# WSL setup

Use the Linux filesystem for the checkout, for example `~/code/dihiggs_llp_recast`, rather than `/mnt/c/...`.

```bash
mkdir -p ~/code
cd ~/code
git clone https://github.com/fbientrigo/dihiggs_llp_recast.git
cd dihiggs_llp_recast
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
make static-check
make bootstrap
make upstream-check
make hep-preflight
make manifest
```

The bootstrap is network-dependent but the tests and manifest utilities are not. Pythia8, FastJet and MadGraph are intentionally not installed automatically: their source, build flags and prefixes must be visible in the validation record.

To compile after installing Pythia8 and FastJet:

```bash
cp configs/toolchain.env.example configs/toolchain.env
$EDITOR configs/toolchain.env
make build-upstream
make manifest
```

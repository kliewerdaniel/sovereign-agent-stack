# Package Manager Distribution

SAS is distributed via multiple package managers for easy installation.

## pip (Python Package Index)

```bash
pip install sovereign-agent-stack
```

Installs the `sas` CLI and all Python dependencies.

## Homebrew (macOS/Linux)

```bash
# Add the tap
brew tap kliewerdaniel/sas

# Install SAS
brew install sovereign-agent-stack

# Upgrade
brew upgrade sovereign-agent-stack
```

### Formula

```ruby
# Formula/sovereign-agent-stack.rb
class SovereignAgentStack < Formula
  desc "Local-first, compile-time AI agent framework"
  homepage "https://github.com/kliewerdaniel/sovereign-agent-stack"
  url "https://github.com/kliewerdaniel/sovereign-agent-stack/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER"
  license "MIT"

  depends_on "python@3.11"

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/pyyaml-6.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  def install
    virtualenv_create(libexec, "python3.11")
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/sas", "--version"
  end
end
```

## apt (Debian/Ubuntu)

```bash
# Add the repository
curl -fsSL https://sas.dev/apt/gpg.key | sudo gpg --dearmor -o /usr/share/keyrings/sas.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/sas.gpg] https://sas.dev/apt stable main" | sudo tee /etc/apt/sources.list.d/sas.list

# Install
sudo apt update
sudo apt install sovereign-agent-stack

# Upgrade
sudo apt upgrade sovereign-agent-stack
```

### DEBIAN/control

```debcontrol
Package: sovereign-agent-stack
Version: 0.1.0
Section: python
Priority: optional
Architecture: amd64
Depends: python3.11, python3-pip
Maintainer: Daniel Kliewer <daniel@danielkliewer.com>
Description: Local-first, compile-time AI agent framework
 A sovereign AI agent framework that owns 6 of 8 layers by default.
```

## Chocolatey (Windows)

```powershell
# Install
choco install sovereign-agent-stack

# Upgrade
choco upgrade sovereign-agent-stack
```

### nuspec

```xml
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>sovereign-agent-stack</id>
    <version>0.1.0</version>
    <title>Sovereign Agent Stack</title>
    <authors>Daniel Kliewer</authors>
    <owners>Daniel Kliewer</owners>
    <licenseUrl>https://github.com/kliewerdaniel/sovereign-agent-stack/blob/main/LICENSE</licenseUrl>
    <projectUrl>https://github.com/kliewerdaniel/sovereign-agent-stack</projectUrl>
    <description>Local-first, compile-time AI agent framework</description>
    <tags>ai agent sovereignty local-first</tags>
    <dependencies>
      <dependency id="python" version="3.11" />
    </dependencies>
  </metadata>
</package>
```

## Docker

```bash
# Pull the image
docker pull ghcr.io/kliewerdaniel/sovereign-agent-stack:latest

# Run the sovereignty dashboard
docker run -v $(pwd)/sas.yaml:/app/sas.yaml ghcr.io/kliewerdaniel/sovereign-agent-stack:latest sas dashboard --config /app/sas.yaml

# Run interactively
docker run -it ghcr.io/kliewerdaniel/sovereign-agent-stack:latest bash
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "sas"]
CMD ["--help"]
```

## Verification

After installation, verify SAS is working:

```bash
# Check version
sas --version

# Initialize a config
python -m sas init --output sas.yaml

# Run the dashboard
python -m sas dashboard --config sas.yaml --verbose
```

## Building from Source

```bash
git clone https://github.com/kliewerdaniel/sovereign-agent-stack.git
cd sovereign-agent-stack
pip install -e ".[dev]"
python -m sas dashboard --verbose
```

## Release Process

1. Bump version in `pyproject.toml` and `src/sas/__init__.py`
2. Tag release: `git tag -a v0.1.0 -m "Release v0.1.0"`
3. Push tag: `git push origin v0.1.0`
4. Build package: `python -m build`
5. Upload to PyPI: `twine upload dist/*`
6. Update Homebrew formula with new SHA256
7. Update apt repository
8. Push Chocolatey package
9. Build and push Docker image

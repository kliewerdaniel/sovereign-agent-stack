class SovereignAgentStack < Formula
  desc "Local-first, compile-time AI agent framework"
  homepage "https://github.com/kliewerdaniel/sovereign-agent-stack"
  url "https://github.com/kliewerdaniel/sovereign-agent-stack/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  depends_on "python@3.11"

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/pyyaml-6.0.tar.gz"
    sha256 "PLACEHOLDER_SHA256"
  end

  resource "pynacl" do
    url "https://files.pythonhosted.org/packages/source/p/pynacl/PyNaCl-1.5.0.tar.gz"
    sha256 "PLACEHOLDER_SHA256"
  end

  resource "numpy" do
    url "https://files.pythonhosted.org/packages/source/n/numpy/numpy-1.24.0.tar.gz"
    sha256 "PLACEHOLDER_SHA256"
  end

  resource "pandas" do
    url "https://files.pythonhosted.org/packages/source/p/pandas/pandas-2.0.0.tar.gz"
    sha256 "PLACEHOLDER_SHA256"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.0.0.tar.gz"
    sha256 "PLACEHOLDER_SHA256"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.28.0.tar.gz"
    sha256 "PLACEHOLDER_SHA256"
  end

  def install
    virtualenv_create(libexec, "python3.11")
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/sas", "--version"
  end
end

class SovereignAgentStack < Formula
  desc "Local-first, compile-time AI agent framework"
  homepage "https://github.com/kliewerdaniel/sovereign-agent-stack"
  url "https://github.com/kliewerdaniel/sovereign-agent-stack/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  depends_on "python@3.11"

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/p/pyyaml/pyyaml-6.0.tar.gz"
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

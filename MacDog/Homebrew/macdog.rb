class Macdog < Formula
  desc "A native macOS network utility for sending files, messages, and creating connections"
  homepage "https://github.com/YourUsername/MacDog"
  url "https://github.com/YourUsername/MacDog/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  license "MIT"
  head "https://github.com/YourUsername/MacDog.git", branch: "main"

  depends_on xcode: ["13.0", :build]
  depends_on macos: :big_sur

  def install
    system "swift", "build", "--disable-sandbox", "--configuration", "release"
    bin.install ".build/release/macdog"
    
    # Install man page
    man1.install "Documentation/macdog.1"
    
    # Generate and install shell completions
    generate_completions_from_executable(bin/"macdog", "--generate-completion-script")
    
    # Install GUI app if it was built
    app_path = "Sources/MacDogGUI/build/Release/MacDog.app"
    if File.exist?(app_path)
      prefix.install app_path
    end
  end

  def caveats
    <<~EOS
      MacDog CLI tool has been installed to:
        #{bin}/macdog
      
      To install the MacDog GUI application to your Applications folder, run:
        ln -sf "#{prefix}/MacDog.app" "/Applications/MacDog.app"
      
      Run 'macdog --help' to see available options.
    EOS
  end

  test do
    # Test that the command-line tool runs and displays help
    assert_match "MacDog - A native macOS network utility", shell_output("#{bin}/macdog --help")
    
    # Test version output
    assert_match(/\d+\.\d+\.\d+/, shell_output("#{bin}/macdog --version"))
  end
end 
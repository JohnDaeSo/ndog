class Macdog < Formula
  desc "A native macOS network utility for sending files, messages, and creating connections"
  homepage "https://github.com/JohnDaeSo/ndog"
  
  # Use a stable reference point (the latest commit SHA as of now)
  url "https://github.com/JohnDaeSo/ndog/archive/ff4a449.tar.gz"
  version "1.0.0-dev"  # Development version
  sha256 :no_check  # Skip checksum verification for now
  license "MIT"
  
  # For development/edge version
  head do
    url "https://github.com/JohnDaeSo/ndog.git", branch: "main"
  end

  # Dependencies
  depends_on xcode: ["13.0", :build]
  depends_on macos: :big_sur

  def install
    # Change to the MacDog directory where the Swift package is located
    cd "MacDog" do
      # Build the CLI tool
      system "swift", "build", "--disable-sandbox", "--configuration", "release"
      
      # Find the built binary path and install it
      libexec.install Dir["**/.build/release/macdog"].first || ".build/release/macdog"
      
      # Create a bin script that runs the installed binary
      bin.write_exec_script libexec/"macdog"
      
      # Only try to install man page if it exists
      man_page = "Documentation/macdog.1"
      man1.install man_page if File.exist?(man_page)
      
      # Only try to install GUI app if it exists
      app_path = "Sources/MacDogGUI/build/Release/MacDog.app"
      prefix.install app_path if File.exist?(app_path)
      
      # Generate shell completions if the binary supports it
      if File.executable?(libexec/"macdog")
        output = Utils.safe_popen_read(libexec/"macdog", "--generate-completion-script", "bash")
        (bash_completion/"macdog").write output if output
        
        output = Utils.safe_popen_read(libexec/"macdog", "--generate-completion-script", "zsh")
        (zsh_completion/"_macdog").write output if output
      end
    end
  end

  def post_install
    # Ensure binary is executable
    chmod 0555, bin/"macdog"
    
    # Link the GUI app to Applications if it exists
    app_path = prefix/"MacDog.app"
    if File.directory?(app_path)
      ln_sf app_path, "/Applications/MacDog.app"
    end
  end

  def caveats
    <<~EOS
      MacDog CLI tool has been installed to:
        #{bin}/macdog
      
      #{File.directory?(prefix/"MacDog.app") ? "MacDog GUI app has been linked to your Applications folder." : "GUI app was not installed (build it separately if needed)."}
      
      Run 'macdog --help' to see available options.
      
      For more information, visit: https://github.com/JohnDaeSo/ndog
    EOS
  end

  test do
    # Basic test: just check if the binary runs
    system bin/"macdog", "--version"
  end
end 
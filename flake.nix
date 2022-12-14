{
  description = "github-tui";

  inputs = {
    nixpkgs = { url = "github:nixos/nixpkgs/nixpkgs-unstable"; };
  };

  outputs = inputs@{ self, nixpkgs, ... }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };

      pythonPackages = pkgs.python3Packages;

      rich = pythonPackages.buildPythonPackage rec {
        pname = "rich";
        version = "12.6.0";
        format = "pyproject";

        src = pkgs.fetchFromGitHub {
          owner = "Textualize";
          repo = pname;
          rev = "v${version}";
          sha256 = "sha256-g3tXftEoBCJ1pMdLyDBXQvY9haGMQkuY1/UBOtUqrLE=";
        };

        nativeBuildInputs = [ pythonPackages.poetry-core ];

        propagatedBuildInputs = [
          pythonPackages.CommonMark
          pythonPackages.pygments
        ];

        doCheck = false;
      };

      nanoid = pythonPackages.buildPythonPackage rec {
        pname = "nanoid";
        version = "2.0.0";

        src = pythonPackages.fetchPypi {
          inherit pname version;
          sha256 = "sha256-WoDK1enG6a46Qfovs0rhiffLQgsqXY+CvZ0jRm5O+mg=";
        };

        doCheck = false;
      };

      textual = pythonPackages.buildPythonPackage rec {
        pname = "textual";
        version = "unstable";
        format = "pyproject";

        src = pkgs.fetchFromGitHub {
          owner = "Textualize";
          repo = "textual";
          rev = "cb96da1a8e0a59dcf7d8343c49e747d54d80fff5";
          sha256 = "sha256-3/auVhzOGl3saGXmixIjOrZa7LYZahYh/Kyw59M5i8w=";
        };

        preConfigure = ''
          substituteInPlace src/textual/drivers/linux_driver.py \
            --replace "termios.tcflush(self.fileno, termios.TCIFLUSH)" "self.exit_event.clear(); termios.tcflush(self.fileno, termios.TCIFLUSH)"
        '';

        nativeBuildInputs = [
          pythonPackages.poetry-core
        ];

        propagatedBuildInputs = [
          rich
          pythonPackages.importlib-metadata
          pythonPackages.typing-extensions
          nanoid

          # dev dependencies
          pythonPackages.click
          pythonPackages.aiohttp
          pythonPackages.msgpack
        ];
      };
    in {
      devShell.x86_64-linux = pkgs.mkShell {
        buildInputs = [
          textual
          pythonPackages.PyGithub

          # development
          pythonPackages.flake8
          pythonPackages.black
        ];

        shellHook = ''
           alias github-tui="textual run --dev github_tui.app:GithubTUI"

           export GITHUB_API_TOKEN=$(password-store get www/github.com/costrouc token-personal)
        '';
      };
    };
}

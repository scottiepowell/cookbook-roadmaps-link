#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir/.." rev-parse --show-toplevel)
cd "$repo_root"

temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT

checks_passed=0

pass() {
  checks_passed=$((checks_passed + 1))
  printf 'PASS: %s\n' "$1"
}

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  printf 'Repository validation failed after %d completed checks.\n' \
    "$checks_passed" >&2
  exit 1
}

check_shell_syntax() {
  bash -n deploy.sh || return 1

  local script
  while IFS= read -r -d '' script; do
    bash -n "$script" || return 1
  done < <(find scripts -maxdepth 1 -type f -name '*.sh' -print0 | sort -z)
}

check_compose_config() {
  command -v docker >/dev/null 2>&1 || {
    echo "Docker is required for Compose validation." >&2
    return 1
  }
  docker compose version >/dev/null 2>&1 || {
    echo "The Docker Compose plugin is required." >&2
    return 1
  }

  local compose_dir="$temp_dir/compose"
  mkdir -p "$compose_dir"
  cp docker-compose.yml "$compose_dir/docker-compose.yml"
  cp .env.example "$compose_dir/.env"
  if [[ -d ai-api ]]; then
    cp -R ai-api "$compose_dir/ai-api"
  fi

  docker compose \
    --project-directory "$compose_dir" \
    --env-file "$compose_dir/.env" \
    -f "$compose_dir/docker-compose.yml" \
    config --quiet
}

check_ai_api_tests() {
  [[ -d ai-api ]] || return 0

  local python_cmd
  if [[ -n "${AI_API_PYTHON:-}" ]]; then
    python_cmd="$AI_API_PYTHON"
  elif command -v python >/dev/null 2>&1; then
    python_cmd=python
  elif command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    python_cmd=python3
  else
    echo "Python is required for AI API tests." >&2
    return 1
  fi

  local venv_dir="$temp_dir/ai-api-venv"
  $python_cmd -m venv "$venv_dir"

  local venv_python
  if [[ -x "$venv_dir/bin/python" ]]; then
    venv_python="$venv_dir/bin/python"
  elif [[ -x "$venv_dir/Scripts/python.exe" ]]; then
    venv_python="$venv_dir/Scripts/python.exe"
  else
    echo "Could not find Python inside temporary AI API virtual environment." >&2
    return 1
  fi

  "$venv_python" -m pip install --disable-pip-version-check -r ai-api/requirements.txt >/dev/null
  PYTHONPATH=ai-api "$venv_python" -m pytest ai-api/tests
}

check_whitespace() {
  if ! git diff --check >/dev/null; then
    return 1
  fi
  if ! git diff --cached --check >/dev/null; then
    return 1
  fi

  local findings="$temp_dir/whitespace-files"
  git ls-files --cached --others --exclude-standard -z |
    perl -0ne '
      chomp;
      my $path = $_;
      next unless -f $path;
      open my $fh, "<", $path or die "Cannot read $path: $!";
      local $/;
      my $data = <$fh>;
      close $fh;
      next if index($data, "\0") >= 0;
      print "$path\n" if $data =~ /[ \t]+$/m;
    ' > "$findings"

  if [[ -s $findings ]]; then
    echo "Trailing whitespace found in:" >&2
    sed 's/^/  /' "$findings" >&2
    return 1
  fi
}

check_markdown_links() {
  local findings="$temp_dir/markdown-link-files"
  git ls-files --cached --others --exclude-standard -z -- '*.md' |
    REPO_ROOT="$repo_root" perl -0ne '
      use File::Basename qw(dirname);
      use File::Spec;
      chomp;
      my $source = $_;
      open my $fh, "<", $source or die "Cannot read $source: $!";
      local $/;
      my $data = <$fh>;
      close $fh;

      while ($data =~ /!?\[[^\]]*\]\(([^)]+)\)/g) {
        my $target = $1;
        $target =~ s/^<|>$//g;
        $target =~ s/[?#].*$//;
        next if $target eq "";
        next if $target =~ m{^(?:[a-z][a-z0-9+.-]*:|//)}i;
        $target =~ s/%20/ /g;
        my $resolved = File::Spec->rel2abs(
          File::Spec->catfile(dirname($source), $target),
          $ENV{REPO_ROOT}
        );
        if (!-e $resolved) {
          print "$source\n";
          last;
        }
      }
    ' | sort -u > "$findings"

  if [[ -s $findings ]]; then
    echo "Broken local Markdown link found in:" >&2
    sed 's/^/  /' "$findings" >&2
    return 1
  fi
}


check_old_domain_references() {
  local findings="$temp_dir/old-domain-files"
  git ls-files --cached --others --exclude-standard -z |
    perl -0ne '
      chomp;
      my $path = $_;
      next if $path =~ m{^(?:inbox|outbox)/};
      next unless -f $path;
      open my $fh, "<", $path or die "Cannot read $path: $!";
      local $/;
      my $data = <$fh>;
      close $fh;
      next if index($data, "\0") >= 0;
      my $old_host = "cookbook" . ".roadmap" . ".links";
      my $old_base = "roadmap" . ".links";
      print "$path\n" if index($data, $old_host) >= 0 || index($data, $old_base) >= 0;
    ' | sort -u > "$findings"

  if [[ -s $findings ]]; then
    echo "Old domain reference found in active files:" >&2
    sed 's/^/  /' "$findings" >&2
    return 1
  fi
}

check_secret_patterns() {
  local findings="$temp_dir/secret-findings"
  git ls-files --cached --others --exclude-standard -z |
    perl -0ne '
      chomp;
      my $path = $_;
      next unless -f $path;
      open my $fh, "<", $path or die "Cannot read $path: $!";
      local $/;
      my $data = <$fh>;
      close $fh;
      next if index($data, "\0") >= 0;

      my @rules = (
        ["AWS access key ID", "A" . "KIA" . "[0-9A-Z]{16}"],
        ["AWS temporary access key ID", "A" . "SIA" . "[0-9A-Z]{16}"],
        ["GitHub token", "gh" . "[pousr]_[A-Za-z0-9_]{20,}"],
        ["OpenAI API key", "s" . "k-[A-Za-z0-9]{20,}"],
        ["Private key header", "BEGIN " . "(?:RSA |EC |OPENSSH )?PRIVATE KEY"],
      );

      for my $rule (@rules) {
        print "$rule->[0]\t$path\n" if $data =~ /$rule->[1]/;
      }

      while ($data =~ /CLOUDFLARE_(?:TUNNEL_)?TOKEN\s*=\s*([^\s"\x27\x60]+)/g) {
        my $value = $1;
        next if $value =~ /^(?:replace_me|example|token)$/i;
        next if $value =~ /^(?:\$|<|\{\{|secrets\.)/;
        if (length($value) >= 20 && $value =~ /^[A-Za-z0-9._-]+$/) {
          print "Cloudflare token assignment\t$path\n";
          last;
        }
      }
    ' | sort -u > "$findings"

  if [[ -s $findings ]]; then
    echo "Possible committed credential detected (rule and file only):" >&2
    while IFS=$'\t' read -r rule path; do
      printf '  %s: %s\n' "$rule" "$path" >&2
    done < "$findings"
    return 1
  fi
}

check_shell_syntax || fail "shell script syntax"
pass "shell script syntax"

check_compose_config || fail "Docker Compose configuration"
pass "Docker Compose configuration"

check_ai_api_tests || fail "AI API tests"
pass "AI API tests"

check_whitespace || fail "whitespace"
pass "whitespace"

check_markdown_links || fail "local Markdown links"
pass "local Markdown links"

check_old_domain_references || fail "old-domain guard"
pass "old-domain guard"

check_secret_patterns || fail "secret-pattern scan"
pass "secret-pattern scan"

printf 'Repository validation passed: %d checks.\n' "$checks_passed"

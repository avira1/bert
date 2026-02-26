#!/usr/bin/env bash
set -euo pipefail

# Export apps/news_digest into a standalone repository named medicare-news-
# Usage:
#   ./apps/news_digest/scripts/export_to_medicare_news_repo.sh /path/to/medicare-news-

TARGET_DIR="${1:-}"
if [[ -z "$TARGET_DIR" ]]; then
  echo "Usage: $0 /absolute/or/relative/path/to/medicare-news-"
  exit 1
fi

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SOURCE_APP_DIR="$SOURCE_ROOT/apps/news_digest"

mkdir -p "$TARGET_DIR"
rsync -a --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  "$SOURCE_APP_DIR/" "$TARGET_DIR/"

if [[ ! -d "$TARGET_DIR/.git" ]]; then
  git -C "$TARGET_DIR" init
fi

if [[ ! -f "$TARGET_DIR/.gitignore" ]]; then
  cat > "$TARGET_DIR/.gitignore" <<'EOF'
.venv/
__pycache__/
.pytest_cache/
*.pyc
EOF
fi

echo "Standalone repo synced to: $TARGET_DIR"
echo "Next steps:"
echo "  cd $TARGET_DIR"
echo "  git add ."
echo "  git commit -m 'Initial import from bert/apps/news_digest'"
echo "  git remote add origin <your-medicare-news--repo-url>"
echo "  git push -u origin main"

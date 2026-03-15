---
name: release
description: Create a new release by bumping version, generating changelog, pushing, and tagging
disable-model-invocation: true
allowed-tools: Bash, Read
argument-hint: [patch|minor|major]
---

kousukanri の新しいリリースを作成する。

## 手順

1. `$ARGUMENTS` からバージョンバンプの種類を判定する（デフォルト: `patch`）
2. 最新タグを取得: !`git tag --sort=-creatordate | head -1`
3. 次のバージョンを算出する（例: v0.2.9 → patch: v0.2.10 / minor: v0.3.0 / major: v1.0.0）
4. 最新タグ以降のコミットを `git log <最新タグ>..HEAD --oneline` で収集する
5. 新しいコミットがなければ中止し、ユーザーに通知する
6. コミットの prefix で分類し、以下の形式でリリースノートを生成する:

```
## 変更点

### 機能追加
- feat: のコミットをここに記載

### 改善
- improvement/refactor 系のコミットをここに記載

### バグ修正
- fix: のコミットをここに記載

### ドキュメント
- docs: のコミットをここに記載
```

該当コミットがあるセクションのみ含める。説明文から prefix（feat:/fix:/docs: 等）は除去する。

7. ユーザーに次のバージョンとリリースノートを提示し、続行の確認を取る
8. 確認後:
   - `git push origin main`
   - アノテーション付きタグを作成: `git tag -a <バージョン> -m "<リリースノート1行目>"`
   - タグをプッシュ: `git push origin <バージョン>`
   - GitHub リリースを作成: `gh release create <バージョン> --title "<バージョン>" --notes "<リリースノート>"`
9. リリース URL をユーザーに報告する

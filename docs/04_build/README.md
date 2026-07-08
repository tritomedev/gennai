# ビルド・デプロイ記録

echo-observer（自作ExApp）と源内Web本体の、実機ビルド・デプロイ・観察の記録。

## ドキュメント一覧（時系列・推奨する読む順）

1. [echo-observer-local-verification.md](./echo-observer-local-verification.md) — 観察用ExApp「echo-observer」のローカル単体検証（正常系＋エッジケース）
2. [genai-web-deploy-record.md](./genai-web-deploy-record.md) — 源内WebのAWSデプロイ記録（アクセスURL・遭遇した制限と対処・撤去方法）
3. [exapp-observation-2026-07-08.md](./exapp-observation-2026-07-08.md) — **本命の成果**。源内Webにecho-observerを登録し、源内が実際に送るリクエストを捕捉。仕様書外フィールド（`sessionId`・`x-user-id`）を発見

## 関連

- 自作ExAppの実装: [apps/echo-observer/](../../apps/echo-observer/)
- 源内プロトコル仕様（実機観察の反映済み）: [docs/02_research/ai-app-api-spec.md](../02_research/ai-app-api-spec.md)
- デプロイ要件・コスト設計: [docs/03_setup/](../03_setup/)

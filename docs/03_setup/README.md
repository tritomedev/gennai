# 環境構築手順

源内Web（genai-web）をAWSにデプロイするための要件・コスト設計・ガードレールをまとめる。

## ドキュメント一覧（推奨する読む順）

1. [genai-web-aws-requirements.md](./genai-web-aws-requirements.md) — **まずここ**。AWSデプロイ要件・必要ツール・手順の全体像（AWSデプロイは回避不能という結論）
2. [genai-web-minimal-param-design.md](./genai-web-minimal-param-design.md) — 最小コスト構成パラメータの設計（WAFなし・モデル最安・RAG地雷なしの確認）
3. [genai-web-aws-cost-breakdown.md](./genai-web-aws-cost-breakdown.md) — `cdk synth` 実データによる全リソースのコスト内訳。**VPC/NAT撤廃（POC）で固定費¥17,000→¥600/月** の実証と対策A/B/C
4. [aws-cost-guardrails.md](./aws-cost-guardrails.md) — コスト事故防止（Budgetsアラート・コストタグ・cdk destroy）の手順

## 実施結果

実際のデプロイ記録は [docs/04_build/genai-web-deploy-record.md](../04_build/genai-web-deploy-record.md) を参照。

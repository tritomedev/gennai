#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { ExAppStack } from '../lib/exapp-stack';

const app = new cdk.App();

new ExAppStack(app, 'GennaiExApps', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? 'ap-northeast-1',
  },
  description: '源内 Ex-App（自作AIアプリ）のホスティング',
});

// 請求をプロジェクト単位で追えるようにする（コスト配分タグの有効化は別途コンソールで行う）
cdk.Tags.of(app).add('Project', 'gennai');
cdk.Tags.of(app).add('Component', 'exapp');

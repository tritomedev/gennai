import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import * as ecrAssets from 'aws-cdk-lib/aws-ecr-assets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as secrets from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';

export interface ExAppProps {
  /** apps/ 配下のディレクトリ名（Dockerfile を置いてある場所） */
  readonly dir: string;
  /** 論理ID・リソース名に使う識別子 */
  readonly name: string;
  /** Lambdaに渡す環境変数（AWS_REGION等の予約名は指定できない） */
  readonly environment?: Record<string, string>;
  /** 新規AWSアカウントは512MB上限。緩和が通るまでは512のままにする */
  readonly memorySize?: number;
}

/**
 * 源内 Ex-App 1本を Lambda（コンテナイメージ）＋ Function URL で公開する。
 *
 * - 源内Webは x-api-key ヘッダーで認証するだけなので Function URL は authType=NONE とし、
 *   キーの検証はアプリ側（main.py の _authorized）で行う。キーの実体は Secrets Manager。
 * - 源内Webの ExApp 呼び出しタイムアウトは29秒（cdk.json の exAppInvokeTimeoutSeconds）。
 *   Lambda側はそれより少し長い30秒にして、源内側で先に切れるようにしている。
 */
export class ExApp extends Construct {
  public readonly functionUrl: string;
  public readonly apiKeySecret: secrets.Secret;

  constructor(scope: Construct, id: string, props: ExAppProps) {
    super(scope, id);

    this.apiKeySecret = new secrets.Secret(this, 'ApiKey', {
      secretName: `gennai/exapp/${props.name}/api-key`,
      description: `源内Webの「APIキー」欄に入力する値（${props.name}）`,
      generateSecretString: {
        excludePunctuation: true,
        includeSpace: false,
        passwordLength: 40,
      },
    });

    const logGroup = new logs.LogGroup(this, 'Logs', {
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const fn = new lambda.DockerImageFunction(this, 'Function', {
      code: lambda.DockerImageCode.fromImageAsset(
        path.join(__dirname, '..', '..', props.dir),
        { platform: ecrAssets.Platform.LINUX_ARM64 }
      ),
      architecture: lambda.Architecture.ARM_64,
      memorySize: props.memorySize ?? 512,
      timeout: cdk.Duration.seconds(30),
      environment: {
        EXAPP_API_KEY_SECRET_ARN: this.apiKeySecret.secretArn,
        ...props.environment,
      },
      logGroup,
    });

    this.apiKeySecret.grantRead(fn);

    // Bedrockはクロスリージョン推論プロファイル（jp.anthropic.*）を使うため、
    // 呼び先が複数リージョンのfoundation-modelに広がる。サンプルアプリのため対象は絞らない。
    fn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['bedrock:InvokeModel', 'bedrock:InvokeModelWithResponseStream'],
        resources: ['*'],
      })
    );

    const url = fn.addFunctionUrl({ authType: lambda.FunctionUrlAuthType.NONE });
    this.functionUrl = url.url;
  }
}

export class ExAppStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const hoikusho = new ExApp(this, 'HoikushoCheck', {
      dir: 'hoikusho-check',
      name: 'hoikusho-check',
      environment: {
        LLM_MODEL: 'jp.anthropic.claude-haiku-4-5-20251001-v1:0',
      },
    });

    const wardRag = new ExApp(this, 'WardMinutesRag', {
      dir: 'ward-minutes-rag',
      name: 'ward-minutes-rag',
      environment: {
        LLM_MODEL: 'jp.anthropic.claude-haiku-4-5-20251001-v1:0',
      },
    });

    new cdk.CfnOutput(this, 'WardMinutesRagUrl', {
      value: wardRag.functionUrl,
      description: '源内Webの「APIエンドポイントのURL」に入力する値',
    });
    new cdk.CfnOutput(this, 'WardMinutesRagApiKeySecret', {
      value: wardRag.apiKeySecret.secretName,
      description: 'APIキーの取得: aws secretsmanager get-secret-value --secret-id <この値>',
    });

    new cdk.CfnOutput(this, 'HoikushoCheckUrl', {
      value: hoikusho.functionUrl,
      description: '源内Webの「APIエンドポイントのURL」に入力する値',
    });
    new cdk.CfnOutput(this, 'HoikushoCheckApiKeySecret', {
      value: hoikusho.apiKeySecret.secretName,
      description: 'APIキーの取得: aws secretsmanager get-secret-value --secret-id <この値>',
    });
  }
}

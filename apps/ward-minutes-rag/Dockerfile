# 源内 Ex-App を AWS Lambda（コンテナイメージ）で動かす。
# ベクトルDBは使わず、埋め込み済みインデックス（data/index）をイメージに同梱して
# メモリ内でコサイン類似度検索を行う（scripts/build_index.py で生成）。
FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt -t ${LAMBDA_TASK_ROOT}

COPY main.py rag.py ${LAMBDA_TASK_ROOT}/
COPY data/index ${LAMBDA_TASK_ROOT}/data/index

CMD ["main.handler"]

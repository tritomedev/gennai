# 源内 Ex-App を AWS Lambda（コンテナイメージ）で動かす。
# ローカルの uvicorn 起動と同じ main:app を Mangum 経由で叩くため、コードは共通。
FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt -t ${LAMBDA_TASK_ROOT}

COPY main.py check.py chat.py llm.py rules.py ${LAMBDA_TASK_ROOT}/

CMD ["main.handler"]

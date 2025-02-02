# h-genai

# Deploying changes to AWS Lambda

```bash
cd server && docker build -t h-genai-server . && docker tag h-genai-server:latest 140023381458.dkr.ecr.us-west-2.amazonaws.com/h-genai-server:latest && docker push 140023381458.dkr.ecr.us-west-2.amazonaws.com/h-genai-server:latest && aws lambda update-function-code --function-name h-genai-server --image-uri 140023381458.dkr.ecr.us-west-2.amazonaws.com/h-genai-server:latest
```

TODO:
- Write full description of the project

basic setup:
- we have to use AWS
- server for business logic
- web-app for user interface

server:
- python 3.11
- fastapi
- weasyprint for pdf generation
- RAG
    - tavily api for search (or perplexity models: sonar-pro)
    - probably jina ai for parsing websites
- package manager: poetry

web-app:
- next.js 15

deployment:
- web app on AWS Amplify
- python server functions on AWS Lambda as dockerfiles

ci/cd:
- code on github
- github actions
- branches server and web-app
- 

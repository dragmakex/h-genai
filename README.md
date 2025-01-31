# h-genai

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

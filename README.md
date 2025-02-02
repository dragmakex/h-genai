# h-genai

# Deploying changes to AWS Lambda

```bash
cd server && docker build -t h-genai-server . && docker tag h-genai-server:latest 140023381458.dkr.ecr.us-west-2.amazonaws.com/h-genai-server:latest && docker push 140023381458.dkr.ecr.us-west-2.amazonaws.com/h-genai-server:latest && aws lambda update-function-code --function-name h-genai-server --image-uri 140023381458.dkr.ecr.us-west-2.amazonaws.com/h-genai-server:latest
```


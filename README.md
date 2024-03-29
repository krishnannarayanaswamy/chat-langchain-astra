# DataStax Astra Chat with LangChain

This repo is an implementation of a locally hosted chatbot specifically focused on question answering 
Built with [LangChain](https://github.com/langchain-ai/langchain/), [FastAPI](https://fastapi.tiangolo.com/), and [Next.js](https://nextjs.org) and DataStax Astra as Vector Store(https://astra.datastax.com).

The app leverages LangChain's streaming support and async API to update the page in real time for multiple users.

## ✅ Running locally
1. Install python 3.10 
2. Install node.js 
2. Change directory `cd ai-assistant`
3. Install backend dependencies: `pip install -r requirements.txt`.
4. Make sure to enter your environment variables to configure the application:
```
export ASTRA_DB_API_ENDPOINT=""
export OPENAI_API_KEY=""
export ASTRA_DB_KEYSPACE="default_keyspace"
export ASTRA_DB_APPLICATION_TOKEN=""

# for tracing
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
export LANGCHAIN_API_KEY=
export LANGCHAIN_PROJECT=

# for other models
export ANTHROPIC_API_KEY=""
export GOOGLE_API_KEY= ""
export FIREWORKS_API_KEY=""
export COHERE_API_KEY=""

```
1. Run the Colab notebook to load data into DataStax Astra.
2. Navigate to the folder `cd backend`
3. Navigate to `constants.py` and change `ASTRA_COLLECTION_NAME =` value to your collection
4. Start the Python backend with `python main.py`.
5. Open another terminal window
6. Install frontend dependencies by running `cd ./frontend`, then `npm install`.
7. Run the frontend build with `npm run build` for frontend.
8. Run the frontend code with `npm run dev` 
9. Open [localhost:3000](http://localhost:3000) in your browser.

## 📚 Technical description

There are two components: 
Question-Answering has the following steps:

1. Given the chat history and new user input, determine what a standalone question would be using GPT-3.5.
2. Given that standalone question, look up relevant documents from the vectorstore.
3. Pass the standalone question and relevant documents to the model to generate and stream the final answer.
4. Generate a trace URL for the current chat session, as well as the endpoint to collect feedback.

## Documentation

Looking to use or modify this Use Case Accelerant for your own needs? We've added a few docs to aid with this:

- **[Concepts](./CONCEPTS.md)**: A conceptual overview of the different components of Chat LangChain. Goes over features like ingestion, vector stores, query analysis, etc.
- **[LangSmith](./LANGSMITH.md)**: A guide on adding robustness to your application using LangSmith. Covers observability, evaluations, and feedback.
- **[Production](./PRODUCTION.md)**: Documentation on preparing your application for production usage. Explains different security considerations, and more.
- **[Deployment](./DEPLOYMENT.md)**: How to deploy your application to production. Covers setting up production databases, deploying the frontend, and more.

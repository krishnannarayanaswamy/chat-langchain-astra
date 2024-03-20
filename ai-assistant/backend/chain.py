import os
from operator import itemgetter
from typing import Dict, List, Optional, Sequence

from langchain_astradb import AstraDBVectorStore
from constants import ASTRA_COLLECTION_NAME
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ingest import get_embeddings_model
from langchain_community.chat_models import ChatAnthropic, ChatCohere
from langchain_fireworks import ChatFireworks
from langchain_core.documents import Document
from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
)
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import (
    ConfigurableField,
    Runnable,
    RunnableBranch,
    RunnableLambda,
    RunnablePassthrough,
    RunnableSequence,
    chain,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langsmith import Client


RESPONSE_TEMPLATE = """\
You are an expert academician, tasked with answering any question \
about Academic content for prepladder.

Generate a comprehensive and informative answer of 200 words or less for the \
given question based solely on the provided search results (URL and content). You must \
only use information from the provided search results. Use an unbiased and \
journalistic tone. Combine search results together into a coherent answer. Do not \
repeat text. Cite search results using [${{number}}] notation. Only cite the most \
relevant results that answer the question accurately. Place these citations at the end \
of the sentence or paragraph that reference them - do not put them all at the end. If \
different results refer to different entities within the same name, write separate \
answers for each entity.

You should use bullet points in your answer for readability. Put citations where they apply
rather than putting them all at the end.

If there is nothing in the context relevant to the question at hand, just say "Hmm, I'm \
sorry and i am not able to answer this question for you now. Please try out our FAQs - https://www.prepladder.com/courses/medical-pg/faqs". Don't try to make up an answer.

Anything between the following `context`  html blocks is retrieved from a knowledge \
bank, not part of the conversation with the user. Don't return the sources or the context documents back.

<context>
    {context} 
<context/>

REMEMBER: If there is no relevant information within the context, just say just say "Hmm, I'm \
sorry and i am not able to answer this question for you now. Please try out our FAQs - https://www.prepladder.com/courses/medical-pg/faqs". Don't try to make up an answer. Anything between the preceding 'context' \
html blocks is retrieved from a knowledge bank, not part of the conversation with the \
user.\
"""

COHERE_RESPONSE_TEMPLATE = """\
You are an expert programmer and problem-solver, tasked with answering any question \
about Academic content.

Generate a comprehensive and informative answer of 200 words or less for the \
given question based solely on the provided search results (URL and content). You must \
only use information from the provided search results. Use an unbiased and \
journalistic tone. Combine search results together into a coherent answer. Do not \
repeat text. Cite search results using [${{number}}] notation. Only cite the most \
relevant results that answer the question accurately. Place these citations at the end \
of the sentence or paragraph that reference them - do not put them all at the end. If \
different results refer to different entities within the same name, write separate \
answers for each entity.

You should use bullet points in your answer for readability. Put citations where they apply
rather than putting them all at the end. 

If there is nothing in the context relevant to the question at hand, just say "Hmm, I'm \
sorry and i am not able to answer this question for you now. Please try out our FAQs - https://www.prepladder.com/courses/medical-pg/faqs". Don't try to make up an answer.

REMEMBER: If there is no relevant information within the context, just say "Hmm, I'm \
sorry and i am not able to answer this question for you now. Please try out our FAQs - https://www.prepladder.com/courses/medical-pg/faqs". Don't try to make up an answer. Anything between the preceding 'context' \
html blocks is retrieved from a knowledge bank, not part of the conversation with the \
user. Don't return the sources or the context documents back.\
"""

REPHRASE_TEMPLATE = """\
Given the following conversation and a follow up question, rephrase the follow up \
question to be a standalone question.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone Question:"""


client = Client()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


token=os.environ['ASTRA_DB_APPLICATION_TOKEN']
api_endpoint=os.environ['ASTRA_DB_API_ENDPOINT']
keyspace=os.environ['ASTRA_DB_KEYSPACE']


class ChatRequest(BaseModel):
    question: str
    chat_history: Optional[List[Dict[str, str]]]


def get_retriever() -> BaseRetriever:
    vstore = AstraDBVectorStore(
        embedding=get_embeddings_model(),
        collection_name=ASTRA_COLLECTION_NAME,
        api_endpoint=api_endpoint,
        token=token,
        namespace=keyspace,
    )
    return vstore.as_retriever(search_kwargs=dict(k=3))


def create_retriever_chain(
    llm: LanguageModelLike, retriever: BaseRetriever
) -> Runnable:
    CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(REPHRASE_TEMPLATE)
    condense_question_chain = (
        CONDENSE_QUESTION_PROMPT | llm | StrOutputParser()
    ).with_config(
        run_name="CondenseQuestion",
    )
    conversation_chain = condense_question_chain | retriever
    return RunnableBranch(
        (
            RunnableLambda(lambda x: bool(x.get("chat_history"))).with_config(
                run_name="HasChatHistoryCheck"
            ),
            conversation_chain.with_config(run_name="RetrievalChainWithHistory"),
        ),
        (
            RunnableLambda(itemgetter("question")).with_config(
                run_name="Itemgetter:question"
            )
            | retriever
        ).with_config(run_name="RetrievalChainWithNoHistory"),
    ).with_config(run_name="RouteDependingOnChatHistory")


def format_docs(docs: Sequence[Document]) -> str:
    formatted_docs = []
    for i, doc in enumerate(docs):
        doc_string = f"<doc id='{i}'>{doc.page_content}</doc>"
        formatted_docs.append(doc_string)
    return "\n".join(formatted_docs)


def serialize_history(request: ChatRequest):
    chat_history = request["chat_history"] or []
    converted_chat_history = []
    for message in chat_history:
        if message.get("human") is not None:
            converted_chat_history.append(HumanMessage(content=message["human"]))
        if message.get("ai") is not None:
            converted_chat_history.append(AIMessage(content=message["ai"]))
    return converted_chat_history


def create_chain(llm: LanguageModelLike, retriever: BaseRetriever) -> Runnable:
    retriever_chain = create_retriever_chain(
        llm,
        retriever,
    ).with_config(run_name="FindDocs")
    context = (
        RunnablePassthrough.assign(docs=retriever_chain)
        .assign(context=lambda x: format_docs(x["docs"]))
        .with_config(run_name="RetrieveDocs")
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", RESPONSE_TEMPLATE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )
    default_response_synthesizer = prompt | llm

    cohere_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", COHERE_RESPONSE_TEMPLATE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )

    @chain
    def cohere_response_synthesizer(input: dict) -> RunnableSequence:
        return cohere_prompt | llm.bind(source_documents=input["docs"])

    response_synthesizer = (
        default_response_synthesizer.configurable_alternatives(
            ConfigurableField("llm"),
            default_key="openai_gpt_3_5_turbo",
            anthropic_claude_2_1=default_response_synthesizer,
            fireworks_mixtral=default_response_synthesizer,
            google_gemini_pro=default_response_synthesizer,
            cohere_command=cohere_response_synthesizer,
        )
        | StrOutputParser()
    ).with_config(run_name="GenerateResponse")
    return (
        RunnablePassthrough.assign(chat_history=serialize_history)
        | context
        | response_synthesizer
    )


llm = ChatOpenAI(
    model="gpt-3.5-turbo-1106",
    streaming=True,
    temperature=0,
).configurable_alternatives(
    # This gives this field an id
    # When configuring the end runnable, we can then use this id to configure this field
    ConfigurableField(id="llm"),
    default_key="openai_gpt_3_5_turbo",
    anthropic_claude_2_1=ChatAnthropic(
        model="claude-2.1",
        max_tokens=16384,
        temperature=0,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", "not_provided"),
    ),
    fireworks_mixtral=ChatFireworks(
        model="accounts/fireworks/models/mixtral-8x7b-instruct",
        temperature=0,
        max_tokens=16384,
        fireworks_api_key=os.environ.get("FIREWORKS_API_KEY", "not_provided"),
    ),
    google_gemini_pro=ChatGoogleGenerativeAI(
        model="gemini-pro",
        temperature=0,
        convert_system_message_to_human=True,
        max_tokens=16384,
        google_api_key=os.environ.get("GOOGLE_API_KEY", "not_provided"),
    ),
    cohere_command=ChatCohere(
        model="command",
        cohere_api_key=os.environ.get("COHERE_API_KEY", "not_provided"),
        temperature=0,
    ),
)

retriever = get_retriever()
answer_chain = create_chain(llm, retriever)



# LangSmith

Observability and evaluations are pivotal to any LLM application looking to be productionized, and improve beyond initial deployment.
For this, we use LangSmith, a tool that encapsulates all the necessary components to monitor and improve your LLM applications.
In addition to these two development tools, LangSmith also offers a feature for managing feedback from users.
Getting real user feedback can be invaluable for improving your LLM application, based on facts from actual users, and not just assumptions/theories.

## Observability

Observability is simple when using LangChain as your LLM framework. In its simplest form, all you need is to set two environment variables:

```shell
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=...
```

LangSmith tracing is already setup in an optimized way for Chat LangChain, and only needs extra configuration if you're extending the application in a way that's not covered by the default tracing.

You may see this further customization throughout the repo, mainly in the form of adding config names to runs:

```python
.with_config(
    run_name="CondenseQuestion",
)
```

You can call `.with_config` on any [LangChain Runnable](https://python.langchain.com/docs/expression_language/) and apply things like a `run_name` as seen above.

When running queries through Chat LangChain, you can expect to see LangSmith traces like this show up on your project:

![LangSmith Traces](./assets/images/langsmith_trace.png)

For more detailed information on LangSmith traces, visit the [LangSmith documentation](https://docs.smith.langchain.com/tracing/).

## Evaluations

Evals are a great way to discover issues with your LLM app, areas where it does not perform well, and track regression. LangSmith has a whole suite of tools to aid you with this.

For in depth walkthroughs and explanations of LangSmith evaluations, visit the [LangSmith documentation](https://docs.smith.langchain.com/evaluation). This doc will only go over setting up and running evals on Chat LangChain.

### Datasets

For Chat LangChain, the team at LangChain has already put together a dataset for evaluating the app.

You can find the dataset [here](https://smith.langchain.com/public/452ccafc-18e1-4314-885b-edd735f17b9d/d).

The first step is to download the LangSmith node SDK:

```shell
pip install langsmith
```

Then, you'll want to define some custom criteria to evaluate your dataset on. Some examples are:

- **Semantic similarity**: How similar your generated response is to the ground truth (dataset answers).
- **LLM as a judge**: Use an LLM to judge and assign a score to your generated response.

Finally, configure your evaluation criteria and use the [`run_on_dataset`](https://api.python.langchain.com/en/latest/smith/langchain.smith.evaluation.runner_utils.run_on_dataset.html#langchain.smith.evaluation.runner_utils.run_on_dataset) function to evaluate your dataset.

Once completed, you'll be able to view the results of your evaluation in the LangSmith dashboard. Using these results, you can improve and tweak your LLM.

## Feedback

Gathering feedback from users is a great way to gather human curated data on what works, what doesn't and how you can improve your LLM application. LangSmith makes tracking and gathering feedback as easy as pie.

Currently, Chat LangChain supports gathering a simple 👍 or 👎, which is then translated into a binary score, and saved to each run in LangSmith. This feedback is then stored in the --you guessed it-- feedback tab of the LangSmith trace:

![LangSmith Feedback](./assets/images/langsmith_feedback.png)

Then, inside LangSmith you can efficiently use this data to visualize and understand your user's feedback, as well as curate datasets by feedback for evaluations.

### Go further

In addition to binary scores for feedback, LangSmith also allows for assigning comments to feedback. This can allow for you to gather more detailed and complex feedback from users, further fueling your human curated dataset for improving your LLM application.
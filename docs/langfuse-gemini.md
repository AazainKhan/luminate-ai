---
source: ⚠️ Jupyter Notebook
title: Observability for Google Gemini Models with Langfuse Integration
sidebarTitle: Google Gemini
logo: /images/integrations/google_gemini_icon.svg
description: Learn how to integrate Langfuse with the Google GenAI SDK for comprehensive tracing and debugging of your AI conversations.
category: Integrations
---

# Trace Google Gemini Models in Langfuse

This notebook shows how to trace and observe Google Gemini models with Langfuse and the Google GenAI SDK. 

> **What is Google Gemini?** [Google Gemini](https://ai.google.dev/gemini-api/docs/libraries) is Google’s family of multimodal generative models (text, images, audio, video, code) available through the Gemini API and Vertex AI, with tiers like Flash and Pro for different speed/quality needs.

> **What is the Google GenAI SDK?** The [Google GenAI SDK](https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview) is a unified client library (Python/JavaScript) that simplifies calling Gemini—handling auth (API key or ADC), streaming, tool/function calling, and safety—so you can integrate models in a few lines.

> **What is Langfuse?** [Langfuse](https://langfuse.com) is an open source platform for LLM observability and monitoring. It helps you trace and monitor your AI applications by capturing metadata, prompt details, token usage, latency, and more.


<Steps>
## Step 1: Install Dependencies

Before you begin, install the necessary packages in your Python environment:



```python
%pip install google-genai openai langfuse openinference-instrumentation-google-genai
```

## Step 2: Configure Langfuse SDK

Next, set up your Langfuse API keys. You can get these keys by signing up for a free [Langfuse Cloud](https://cloud.langfuse.com/) account or by [self-hosting Langfuse](https://langfuse.com/self-hosting). These environment variables are essential for the Langfuse client to authenticate and send data to your Langfuse project.

Also set your Google Vertex API credentials which uses Application Default Credentials (ADC) from a service account key file.


```python
import os

# Get keys for your project from the project settings page: https://cloud.langfuse.com
os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-..." 
os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-..." 
os.environ["LANGFUSE_BASE_URL"] = "https://cloud.langfuse.com" # 🇪🇺 EU region
# os.environ["LANGFUSE_BASE_URL"] = "https://us.cloud.langfuse.com" # 🇺🇸 US region

# Your Google Gemini API key
os.environ["GOOGLE_API_KEY"] = "***"  
```

With the environment variables set, we can now initialize the Langfuse client. `get_client()` initializes the Langfuse client using the credentials provided in the environment variables.


```python
from langfuse import get_client

# Initialise Langfuse client and verify connectivity
langfuse = get_client()
assert langfuse.auth_check(), "Langfuse auth failed - check your keys ✋"
```

## Step 3: OpenTelemetry Instrumentation

Use the [`GoogleGenAIInstrumentor`](https://github.com/Arize-ai/openinference/tree/main/python/instrumentation/openinference-instrumentation-google-genai) library to wrap [Google GenAI SDK](https://ai.google.dev/gemini-api/docs/libraries) calls and send OpenTelemetry spans to Langfuse.


```python
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor

GoogleGenAIInstrumentor().instrument()
```

## Step 4: Run an Example


```python
from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is Langfuse?",
)
print(response.text)
```


```python
# Streaming Example
for chunk in client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents="What is Langfuse?",
):
    print(chunk.text, end="", flush=True)
print()  # newline after streaming
```

### View Traces in Langfuse

After executing the application, navigate to your Langfuse Trace Table. You will find detailed traces of the application's execution, providing insights into the agent conversations, LLM calls, inputs, outputs, and performance metrics. 

![Langfuse Trace](https://langfuse.com/images/cookbook/integration_gemini/gemini-trace.png)

[View trace in Langfuse](https://cloud.langfuse.com/project/cloramnkj0002jz088vzn1ja4/traces/9f2f0fe0228fd81a9fe75882934b384a?timestamp=2025-08-01T13%3A22%3A00.147Z&display=details&observation=b7a63ca7e1d083bc)
</Steps>



import { Tabs, Cards } from "nextra/components";
import {
  FileText,
  ClipboardCheck,
  Scale,
  Database,
  LayoutDashboard,
  TestTube,
} from "lucide-react";

## Interoperability with the Python SDK

You can use this integration together with the Langfuse [Python SDK](/docs/observability/sdk/python/overview) to add additional attributes to the trace.

<Tabs items={["Decorator", "Context Manager"]}>
<Tabs.Tab>

The [`@observe()` decorator](/docs/observability/sdk/python/instrumentation#custom-instrumentation) provides a convenient way to automatically wrap your instrumented code and add additional attributes to the trace.

```python
from langfuse import observe, propagate_attributes, get_client
 
langfuse = get_client()
 
@observe()
def my_llm_pipeline(input):
    # Add additional attributes (user_id, session_id, metadata, version, tags) to all spans created within this execution scope
    with propagate_attributes(
        user_id="user_123",
        session_id="session_abc",
        tags=["agent", "my-trace"],
        metadata={"email": "user@langfuse.com"},
        version="1.0.0"
    ):

        # YOUR APPLICATION CODE HERE
        result = call_llm(input)

        # Update the trace input and output
        langfuse.update_current_trace(
            input=input,
            output=result,
        )

        return result
```

Learn more about using the Decorator in the [Python SDK](/docs/observability/sdk/python/instrumentation#custom-instrumentation) docs.

</Tabs.Tab>
<Tabs.Tab>

The [Context Manager](/docs/observability/sdk/python/instrumentation#custom-instrumentation) allows you to wrap your instrumented code using context managers (with `with` statements), which allows you to add additional attributes to the trace.

```python
from langfuse import get_client, propagate_attributes

langfuse = get_client()

with langfuse.start_as_current_observation(as_type="span", name="my-trace") as span:
    # Add additional attributes (user_id, session_id, metadata, version, tags) to all spans created within this execution scope
    with propagate_attributes(
        user_id="user_123",
        session_id="session_abc",
        metadata={"experiment": "variant_a", "env": "prod"},
        version="1.0"
    ):
    
        # YOUR APPLICATION CODE HERE
        result = call_llm("some input")

        # Update the trace input and output
        langfuse.start_as_current_observation(
            input=input,
            output=result,
        )

# Flush events in short-lived applications
langfuse.flush()
```

Learn more about using the Context Manager in the [Python SDK](/docs/observability/sdk/python/instrumentation#custom-instrumentation) docs.

</Tabs.Tab>
</Tabs>

## Next Steps

Once you have instrumented your code, you can manage, evaluate and debug your application:



import { Tabs, Cards } from "nextra/components";
import {
  FileText,
  ClipboardCheck,
  Scale,
  Database,
  LayoutDashboard,
  TestTube,
} from "lucide-react";

{/* wihtout defining num, the cards will be rendered as three columns which is hard to read */}
<Cards num={2}> 
  <Cards.Card
    title="Manage prompts in Langfuse"
    href="/docs/prompts/get-started"
    icon={<FileText />}
  />
  <Cards.Card
    title="Add evaluation scores"
    href="/docs/evaluation/features/evaluation-methods/custom-scores"
    icon={<ClipboardCheck />}
  />
  <Cards.Card
    title="Run LLM-as-a-judge Evaluators"
    href="/docs/scores/model-based-evals"
    icon={<Scale />}
  />
  <Cards.Card
    title="Create datasets"
    href="/docs/datasets/overview"
    icon={<Database />}
  />
  <Cards.Card
    title="Create custom dashboards"
    href="/docs/analytics/custom-dashboards"
    icon={<LayoutDashboard />}
  />
  <Cards.Card
    title="Test queries in the Playground"
    href="/docs/playground"
    icon={<TestTube />}
  />
</Cards>




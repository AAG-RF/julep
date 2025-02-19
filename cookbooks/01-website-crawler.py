import os
import uuid
import yaml
from julep import Client

# Global UUID is generated for agent and task
AGENT_UUID = uuid.uuid4()
TASK_UUID = uuid.uuid4()

# Creating Julep Client with the API Key
api_key = os.getenv("JULEP_API_KEY")
if not api_key:
    raise ValueError("JULEP_API_KEY not found in environment variables")

client = Client(api_key=api_key, environment="dev")

# Creating an "agent"
name = "Jarvis"
about = "The original AI conscious the Iron Man."

# Create the agent
agent = client.agents.create_or_update(
    agent_id=AGENT_UUID,
    name=name,
    about=about,
    model="gpt-4o",
)

# Defining a Task
task_def = yaml.safe_load(f"""
name: Crawling Task

# Define the tools that the agent will use in this workflow
tools:
- name: spider_crawler
  type: integration
  integration:
    provider: spider
    setup:
      spider_api_key: "{spider_api_key}"

# Define the steps of the workflow
main:

# Define a tool call step that calls the spider_crawler tool with the url input
- tool: spider_crawler
  arguments:
    url: "_['url']" # You can also use 'inputs[0]['url']'
    params:
      request: "'smart_mode'"
      limit: "1"
      return_format: "'markdown'"
      proxy_enabled: "True"
      filter_output_images: "True"
      filter_output_svg: "True"
      readability: "True"

# Evaluate step to create a summary of the results
- evaluate:
    documents: |
      " ".join(
      list(
        page['content'] for page in _['result']
        )
      )
      
# Prompt step to create a summary of the results
- prompt: |
    You are {{{{agent.about}}}}
    I have given you this url: {{{{inputs[0]['url']}}}}
    And you have crawled that website. Here are the results you found:
    {{{{_['documents']}}}}
    I want you to create a short summary (no longer than 100 words) of the results you found while crawling that website.

  unwrap: True
""")

# Creating/Updating a task
task = client.tasks.create_or_update(
    task_id=TASK_UUID,
    agent_id=AGENT_UUID,
    **task_def
)

# Creating an Execution
execution = client.executions.create(
    task_id=TASK_UUID,
    input={}
)

# Waiting for the execution to complete
import time
time.sleep(5)

# Getting the execution details
execution = client.executions.get(execution.id)
print("Execution output:", execution.output)

# Listing all the steps of a defined task
transitions = client.executions.transitions.list(execution_id=execution.id).items
print("Execution Steps:")
for transition in transitions:
    print(transition)

# Stream the steps of the defined task
print("Streaming execution transitions:")
print(client.executions.transitions.stream(execution_id=execution.id))
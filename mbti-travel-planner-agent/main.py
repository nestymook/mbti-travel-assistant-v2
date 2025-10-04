from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
app = BedrockAgentCoreApp()

# Change the foundation model here
# model = BedrockModel(model_id="<your-old-model-id>")
model = BedrockModel(model_id="amazon.nova-pro-v1:0")

agent = Agent(model=model)

@app.entrypoint
def invoke(payload): 
    """Your AI agent function""" 
    user_message = payload.get("prompt", "Hello! How can I help you today?") 
    result = agent(user_message) 
    return {"result": result.message}
if __name__ == "__main__": 
    app.run()
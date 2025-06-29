from agno.models.ollama import Ollama
from agno.agent import Agent


def initialize_agents(selected_model, composio_key):
        # Initialize Together AI LLM
        llm = Ollama(id="selected_model")
        
        # Set up Composio tools
        toolset = ComposioToolSet(api_key=composio_key)
        composio_tools = toolset.get_tools(actions=[
            Action.COMPOSIO_SEARCH_TAVILY_SEARCH, 
            Action.PERPLEXITYAI_PERPLEXITY_AI_SEARCH, 
            Action.GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN
        ])

    # Function to create agents
def create_agents(llm, composio_tools):
        # Create the question generator agent
        question_generator = Agent(
            name="Question Generator",
            model=llm,
            instructions="""
            You are an expert at breaking down research topics into specific questions.
            Generate exactly 5 specific yes/no research questions about the given topic in the specified domain.
            Respond ONLY with the text of the 5 questions formatted as a numbered list, and NOTHING ELSE.
            """
        )
        
        return question_generator

    # Function to research a specific question
def research_question(llm, composio_tools, topic, domain, question):
        research_task = Agent(
            model=llm,
            tools=[composio_tools],
            instructions=f"You are a sophisticated research assistant. Answer the following research question about the topic '{topic}' in the domain '{domain}':\n\n{question}\n\nUse the PERPLEXITYAI_PERPLEXITY_AI_SEARCH and COMPOSIO_SEARCH_TAVILY_SEARCH tools to provide a concise, well-sourced answer."
        )

        research_result = research_task.run()
        return research_result.content
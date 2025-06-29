import os
import asyncio
import streamlit as st
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.reasoning import ReasoningTools 

import hydra
import logging
from omegaconf.omegaconf import OmegaConf
from hydra.core.global_hydra import GlobalHydra

# Import your custom modules
from src.processing import extract_questions_after_think
from src.tools import duckduckgo_search, searxng_search, save_report_as_html

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Function to initialize the LLM and tools
def initialize_agents(selected_model, search_tools):
    """Initialize the LLM with the selected model"""
    llm = Ollama(id=selected_model)  # Fixed: use selected_model instead of "selected_model"
    return llm, search_tools

# Function to create agents
def create_agents(llm, search_tools):
    """Create the question generator agent"""
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

# Function to generate research questions
def generate_questions(llm, search_tools, topic, domain):
    """Generate research questions for the given topic and domain"""
    question_generator = create_agents(llm, search_tools)
    
    with st.spinner("🤖 Generating research questions..."):
        questions_task = question_generator.run(
            f"Generate exactly 5 specific yes/no research questions about the topic '{topic}' in the domain '{domain}'."
        )
        questions_text = questions_task.content
        questions_only = extract_questions_after_think(questions_text)
        
        # Extract questions into a list
        questions_list = [q.strip() for q in questions_only.split('\n') if q.strip()]
        st.session_state.questions = questions_list
        return questions_list

# Function to research a specific question
def research_question(llm, search_tools, topic, domain, question):
    """Research a specific question using available search tools"""
    # Create a simple search function that uses your tools
    def search_function(query):
        # Use both DuckDuckGo and SearXNG for comprehensive results
        ddg_results = duckduckgo_search(query, max_results=3)
        searx_results = searxng_search(query, max_results=3)
        
        # Combine results
        all_results = ddg_results.get('results', []) + searx_results.get('results', [])
        return all_results
    
    research_agent = Agent(
        name="Research Agent",
        model=llm,
        instructions=f"""
        You are a sophisticated research assistant. Answer the following research question about the topic '{topic}' in the domain '{domain}':

        {question}

        Use the available search tools to find relevant information and provide a concise, well-sourced answer.
        Include specific facts, statistics, and cite sources where possible.
        """
    )
    
    # Perform search and get results
    search_query = f"{topic} {domain} {question}"
    search_results = search_function(search_query)
    
    # Format search results for the agent
    formatted_results = "\n".join([
        f"Title: {result.get('title', 'N/A')}\nURL: {result.get('url', 'N/A')}\nContent: {result.get('content', 'N/A')}\n"
        for result in search_results[:5]  # Limit to top 5 results
    ])
    
    research_result = research_agent.run(
        f"Based on the following search results, answer the question: {question}\n\nSearch Results:\n{formatted_results}"
    )
    return research_result.content

# Function to compile final report
def compile_report(llm, search_tools, topic, domain, question_answers):
    """Compile the final research report"""
    with st.spinner("📝 Compiling final report..."):
        qa_sections = "\n".join(
            f"<h2>{idx+1}. {qa['question']}</h2>\n<p>{qa['answer']}</p>" 
            for idx, qa in enumerate(question_answers)
        )
        
        report_compiler = Agent(
            name="Report Compiler",
            model=llm,
            instructions=f"""
            You are a sophisticated research assistant. Compile the following research findings into a professional, McKinsey-style report. The report should be structured as follows:

            1. Executive Summary/Introduction: Briefly introduce the topic and domain, and summarize the key findings.
            2. Research Analysis: For each research question, create a section with a clear heading and provide a detailed, analytical answer. Do NOT use a Q&A format; instead, weave the answer into a narrative and analytical style.
            3. Conclusion/Implications: Summarize the overall insights and implications of the research.

            Use clear, structured HTML for the report.

            Topic: {topic}
            Domain: {domain}

            Research Questions and Findings (for your reference):
            {qa_sections}

            Create a comprehensive, professional report in HTML format.
            """
        )
        
        compile_result = report_compiler.run()
        report_content = compile_result.content
        
        # Save report to local file
        report_title = f"{topic}_{domain}_research_report"
        save_result = save_report_as_html(report_title, report_content)
        st.success(f"Report compiled successfully! {save_result}")
        
        st.session_state.report_content = report_content
        st.session_state.research_complete = True
        return report_content

@hydra.main(config_path="./config", config_name="config", version_base=None)
def main(cfg):
    """Main application function"""
    logger.info(OmegaConf.to_yaml(cfg, resolve=True))
    logger.info(f"Using the model: {cfg.model.COLLECTION_NAME}")
    
    # Constants
    COLLECTION_NAME = cfg.model.COLLECTION_NAME
    search_tools = cfg.web_search.search_options

    # Initialize session state
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'question_answers' not in st.session_state:
        st.session_state.question_answers = []
    if 'report_content' not in st.session_state:
        st.session_state.report_content = ""
    if 'research_complete' not in st.session_state:
        st.session_state.research_complete = False
    if 'model_version' not in st.session_state:
        st.session_state.model_version = cfg.model.model

    # Set page config
    st.set_page_config(
        page_title="AI DeepResearch Agent",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.title("🔍 AI DeepResearch Agent with Agno and Ollama")

    ##################### Sidebar configuration #####################
    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", width=200)

    st.sidebar.header("🤖 Configuration")

    # Model Selection
    st.sidebar.header("📦 Model Selection")

    model_help = """
    - 1.5b: Lighter model, suitable for most laptops
    - 4b: More capable but requires better GPU/RAM

    Choose based on your hardware capabilities.
    """

    st.session_state.model_version = st.sidebar.selectbox(
        "Select Model Version",
        options=list(cfg.model.available_models),
        help=model_help
    )

    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info(
        "This AI DeepResearch Agent application uses Ollama local models and search tools to perform comprehensive research on any topic. "
        "It generates research questions, finds answers, and compiles a professional report."
    )

    st.sidebar.markdown("### Search Tools Used")
    st.sidebar.markdown("- 🦆 DuckDuckGo Search")
    st.sidebar.markdown("- 🌀 SearXNG Search")

    #############################################################################################

    # Check if required environment variables are set
    required_env_vars = ["SEARXNG_URL"]  # Add other required env vars as needed
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if not missing_vars:
        # Initialize agents
        llm, search_tools_config = initialize_agents(st.session_state.model_version, search_tools)
        
        # Main content area
        st.header("Research Topic")
        
        # Input fields
        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("What topic would you like to research?", placeholder="Morocco's Economic Growth")
        with col2:
            domain = st.text_input("What domain is this topic in?", placeholder="National, Regional, Technology, etc.")
        
        # Generate questions section
        if topic and domain and st.button("Generate Research Questions", key="generate_questions"):
            # Generate questions
            questions = generate_questions(llm, search_tools_config, topic, domain)
            
            # Display the generated questions
            st.header("Research Questions")
            for i, question in enumerate(questions):
                st.markdown(f"**{i+1}. {question}**")
        
        # Research section - only show if we have questions
        if st.session_state.questions and st.button("Start Research", key="start_research"):
            st.header("Research Results")
            
            # Reset answers
            question_answers = []
            
            # Research each question
            progress_bar = st.progress(0)
            
            for i, question in enumerate(st.session_state.questions):
                # Update progress
                progress_bar.progress((i) / len(st.session_state.questions))
                
                # Research the question
                with st.spinner(f"🔍 Researching question {i+1}..."):
                    answer = research_question(llm, search_tools_config, topic, domain, question)
                    question_answers.append({"question": question, "answer": answer})
                
                # Display the answer
                st.subheader(f"Question {i+1}:")
                st.markdown(f"**{question}**")
                st.markdown(answer)
                
                # Update progress again
                progress_bar.progress((i + 1) / len(st.session_state.questions))
            
            # Store the answers
            st.session_state.question_answers = question_answers
            
        # Compile report button - show if we have answers
        if st.session_state.question_answers and st.button("Compile Final Report", key="compile_report"):
            report_content = compile_report(llm, search_tools_config, topic, domain, st.session_state.question_answers)
            
            # Display the report content
            st.header("Final Report")
            
            # Show the full report content
            with st.expander("View Full Report Content", expanded=True):
                st.markdown(report_content, unsafe_allow_html=True)
        
        # Display previous results if available
        if len(st.session_state.question_answers) > 0 and not st.session_state.research_complete:
            st.header("Previous Research Results")
            
            # Display research results
            for i, qa in enumerate(st.session_state.question_answers):
                with st.expander(f"Question {i+1}: {qa['question']}"):
                    st.markdown(qa['answer'])
        
        # Display final report if available
        if st.session_state.research_complete and st.session_state.report_content:
            st.header("Final Report")
            
            # Display the report content
            st.success("Your report has been compiled and saved locally.")
            
            # Show the full report content
            with st.expander("View Full Report Content", expanded=True):
                st.markdown(st.session_state.report_content, unsafe_allow_html=True)

    else:
        # Missing environment variables
        st.warning(f"⚠️ Please set the following environment variables: {', '.join(missing_vars)}")
        
        # Example UI
        st.header("How It Works")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("1️⃣ Define Topic")
            st.write("Enter your research topic and domain to begin the research process.")
        
        with col2:
            st.subheader("2️⃣ Generate Questions")
            st.write("The AI generates specific research questions to explore your topic in depth.")
            
        with col3:
            st.subheader("3️⃣ Compile Report")
            st.write("Research findings are compiled into a professional report and saved locally.")

if __name__ == "__main__":
    
    GlobalHydra.instance().clear() # Clear any previous configurations sinon il y'a erreur disant qu'il y'a déja une instance qui fonctionne.
    main()
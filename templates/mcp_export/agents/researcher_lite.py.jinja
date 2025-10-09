"""
Researcher Agent - Lite Implementation

Specializes in information gathering, research, and fact-finding.
"""

from .base_agent import BaseLiteAgent


class ResearcherLiteAgent(BaseLiteAgent):
    """Lite implementation of the Researcher agent."""

    def __init__(self):
        """Initialize the Researcher agent."""
        super().__init__("researcher")

    def _build_prompt(self, instruction: str) -> str:
        """
        Build the researcher-specific prompt.

        Args:
            instruction: The research task

        Returns:
            Formatted prompt for research
        """
        system_prompt = """You are a Research Specialist AI assistant.

Your role is to:
1. Gather comprehensive information on the given topic
2. Identify key facts, trends, and insights
3. Provide well-structured research findings
4. Include relevant context and background
5. Note important sources and references when applicable

Research Approach:
- Start with a broad understanding of the topic
- Identify key aspects and subtopics
- Focus on accuracy and relevance
- Present findings in a clear, organized manner
- Highlight important discoveries and patterns"""

        user_prompt = f"""Research Task: {instruction}

Please conduct thorough research on this topic and provide:
1. Key Information: Main facts and findings
2. Context: Relevant background and related concepts
3. Insights: Important patterns or trends identified
4. Summary: Concise overview of the research findings

Deliver a comprehensive research report focusing on accuracy and relevance."""

        return f"{system_prompt}\n\n{user_prompt}"

    def _post_process(self, response: str) -> str:
        """
        Post-process the research response.

        Args:
            response: Raw LLM response

        Returns:
            Processed research report
        """
        # Add section markers if not present
        if "## Key Information" not in response and "## " not in response:
            # Structure the response if it's unstructured
            lines = response.strip().split('\n')
            structured = ["# Research Report\n"]

            # Try to identify and structure sections
            current_section = []
            for line in lines:
                if line.strip():
                    current_section.append(line)

            if current_section:
                structured.append("## Research Findings\n")
                structured.extend(current_section)

            return '\n'.join(structured)

        return response
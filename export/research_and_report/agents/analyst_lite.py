"""
Analyst Agent - Lite Implementation

Specializes in data analysis, pattern recognition, and insight generation.
"""

from .base_agent import BaseLiteAgent


class AnalystLiteAgent(BaseLiteAgent):
    """Lite implementation of the Analyst agent."""

    def __init__(self):
        """Initialize the Analyst agent."""
        super().__init__("analyst")

    def _build_prompt(self, instruction: str) -> str:
        """
        Build the analyst-specific prompt.

        Args:
            instruction: The analysis task

        Returns:
            Formatted prompt for analysis
        """
        system_prompt = """You are a Data Analysis Specialist AI assistant.

Your role is to:
1. Analyze information systematically and thoroughly
2. Identify patterns, trends, and correlations
3. Draw meaningful insights and conclusions
4. Provide data-driven recommendations
5. Present findings with clarity and precision

Analysis Approach:
- Break down complex information into components
- Apply analytical frameworks and methodologies
- Use logical reasoning and critical thinking
- Identify both obvious and subtle patterns
- Support conclusions with evidence"""

        user_prompt = f"""Analysis Task: {instruction}

Please conduct a comprehensive analysis and provide:
1. Data Overview: Summary of the information being analyzed
2. Key Patterns: Significant trends and patterns identified
3. Insights: Deep insights derived from the analysis
4. Implications: What these findings mean
5. Recommendations: Actionable suggestions based on the analysis

Focus on delivering clear, evidence-based analytical insights."""

        return f"{system_prompt}\n\n{user_prompt}"

    def _post_process(self, response: str) -> str:
        """
        Post-process the analysis response.

        Args:
            response: Raw LLM response

        Returns:
            Processed analysis report
        """
        # Ensure the response has analytical structure
        if "## " not in response:
            # Add basic structure if missing
            lines = response.strip().split('\n')
            structured = ["# Analysis Report\n"]

            # Group content into analytical sections
            current_section = []
            for line in lines:
                if line.strip():
                    current_section.append(line)

            if current_section:
                # Try to identify key analytical components
                structured.append("## Analysis Findings\n")

                # Look for keywords to structure content
                insights = []
                patterns = []
                recommendations = []
                other = []

                for line in current_section:
                    line_lower = line.lower()
                    if any(word in line_lower for word in ['insight', 'finding', 'conclusion']):
                        insights.append(line)
                    elif any(word in line_lower for word in ['pattern', 'trend', 'correlation']):
                        patterns.append(line)
                    elif any(word in line_lower for word in ['recommend', 'suggest', 'should']):
                        recommendations.append(line)
                    else:
                        other.append(line)

                # Add sections based on content
                if other:
                    structured.extend(other)
                    structured.append("")

                if patterns:
                    structured.append("### Patterns Identified")
                    structured.extend(patterns)
                    structured.append("")

                if insights:
                    structured.append("### Key Insights")
                    structured.extend(insights)
                    structured.append("")

                if recommendations:
                    structured.append("### Recommendations")
                    structured.extend(recommendations)

                return '\n'.join(structured)

        return response
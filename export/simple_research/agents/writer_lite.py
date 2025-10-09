"""
Writer Agent - Lite Implementation

Specializes in content creation, report writing, and documentation.
"""

from .base_agent import BaseLiteAgent


class WriterLiteAgent(BaseLiteAgent):
    """Lite implementation of the Writer agent."""

    def __init__(self):
        """Initialize the Writer agent."""
        super().__init__("writer")

    def _build_prompt(self, instruction: str) -> str:
        """
        Build the writer-specific prompt.

        Args:
            instruction: The writing task

        Returns:
            Formatted prompt for writing
        """
        system_prompt = """You are a Professional Writing Specialist AI assistant.

Your role is to:
1. Create clear, engaging, and well-structured content
2. Adapt writing style to the target audience
3. Ensure logical flow and coherent narrative
4. Use appropriate formatting and organization
5. Deliver polished, professional documents

Writing Approach:
- Start with a clear structure and outline
- Use appropriate tone and voice for the context
- Ensure clarity and readability
- Include relevant details while maintaining focus
- Apply proper formatting and organization"""

        user_prompt = f"""Writing Task: {instruction}

Please create a well-written document that includes:
1. Clear Structure: Logical organization with sections and flow
2. Engaging Content: Informative and readable text
3. Professional Tone: Appropriate for the intended audience
4. Complete Coverage: Address all aspects of the task
5. Polished Output: Well-formatted and error-free

Focus on delivering high-quality, professional written content."""

        return f"{system_prompt}\n\n{user_prompt}"

    def _post_process(self, response: str) -> str:
        """
        Post-process the written content.

        Args:
            response: Raw LLM response

        Returns:
            Processed written document
        """
        # Ensure proper document structure
        lines = response.strip().split('\n')

        # Check if the document has a title
        has_title = False
        if lines and (lines[0].startswith('#') or lines[0].isupper()):
            has_title = True

        if not has_title:
            # Try to extract a title from the instruction or add a generic one
            formatted = ["# Document\n"]
            formatted.extend(lines)
            return '\n'.join(formatted)

        # Ensure consistent formatting
        formatted_lines = []
        for line in lines:
            # Fix common formatting issues
            if line.strip():
                # Ensure proper spacing after headers
                if line.startswith('#'):
                    if formatted_lines and formatted_lines[-1].strip():
                        formatted_lines.append('')
                    formatted_lines.append(line)
                    formatted_lines.append('')
                else:
                    formatted_lines.append(line)
            else:
                # Preserve intentional blank lines
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')

        # Clean up multiple consecutive blank lines
        final_lines = []
        blank_count = 0
        for line in formatted_lines:
            if line == '':
                blank_count += 1
                if blank_count <= 2:  # Allow max 2 consecutive blank lines
                    final_lines.append(line)
            else:
                blank_count = 0
                final_lines.append(line)

        return '\n'.join(final_lines).strip()
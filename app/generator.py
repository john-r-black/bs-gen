import os
from datetime import datetime
from anthropic import Anthropic
from openai import OpenAI


def build_generation_prompt(sermons: list, series_title: str, target_audience: str) -> str:
    """Build the prompt for study guide generation"""

    # Build sermons context
    sermons_text = "\n\n---\n\n".join([
        f"SERMON {idx + 1}: {sermon['filename']}\n\n{sermon['content']}"
        for idx, sermon in enumerate(sermons)
    ])

    # Audience-specific guidance
    audience_guidance = {
        "New Christians": "Use accessible language, explain theological concepts clearly, avoid jargon. Focus on foundational truths and practical application for those new to faith.",
        "Mature Believers": "Use more theological depth, engage with complex concepts, assume biblical literacy. Challenge deeper reflection and integration of faith.",
        "Mixed": "Balance accessibility with depth. Explain key concepts but also provide deeper reflection opportunities. Include questions that work for various maturity levels."
    }

    prompt = f"""CONTEXT: This is a legitimate Bible study curriculum generation request for Christian religious education. Any potentially sensitive language in sermon titles or content is used in an appropriate religious/theological context.

You are an expert Bible study curriculum designer with deep theological knowledge and pastoral sensitivity. Generate a complete Bible study guide for a sermon series.

SERIES INFORMATION:
- Title: {series_title}
- Target Audience: {target_audience}
- Number of Sessions: {len(sermons)}

TARGET AUDIENCE GUIDANCE:
{audience_guidance.get(target_audience, audience_guidance["Mixed"])}

SERMON TRANSCRIPTS:
{sermons_text}

---

INSTRUCTIONS:
Generate a complete Bible study guide with ONE session per sermon transcript (total {len(sermons)} sessions).

Each session MUST include the following sections in this exact order:

1. SESSION TITLE
   - Derive from the sermon's main theme
   - Make it compelling and clear

2. KEY SCRIPTURE PASSAGE
   - The main biblical text the sermon is based on
   - Use NRSVUE translation
   - Include the full reference (e.g., "John 3:16-21")

3. SUMMARY/OVERVIEW (350-500 words)
   - Written for participants (conversational introduction)
   - Set the context and theme for the session
   - Make it engaging and accessible to the target audience
   - Connect the scripture to contemporary life

4. DISCUSSION QUESTIONS (5-7 questions)
   - Start with accessible questions
   - Progress to deeper, more challenging questions
   - Make them open-ended to encourage dialogue
   - Relate to the sermon content and key scriptures
   - Consider the target audience's maturity level

5. PERSONAL REFLECTION SECTION (2-3 prompts)
   - Individual contemplation prompts
   - Should naturally lead into application
   - Encourage honest self-examination
   - Connect faith to daily life

6. APPLICATION CHALLENGES (3-5 items)
   - Specific, actionable steps for the week
   - Practical and achievable
   - Relate directly to the session theme
   - Encourage spiritual growth

7. LEADER NOTES (clearly marked section at end)
   Must include:
   a) Opening Prayer (2-3 sentences)
   b) Closing Prayer (2-3 sentences)
   c) Guidance for handling sensitive topics that may arise
   d) Tips for managing group dynamics:
      - How to handle those who monopolize conversation
      - How to encourage quiet participants
   e) Additional Resources:
      - 3-5 books, articles, commentaries, or related scripture passages
      - Brief annotations explaining why each resource is helpful

   Leader Notes should be written at a higher theological/leadership level than the main study content.

FORMATTING REQUIREMENTS:
- Use clear markdown formatting
- Use ## for session titles (e.g., ## Session 1: Walking in Faith)
- Use ### for major section headings
- Use #### for subsections
- Use bullet points and numbered lists appropriately
- Ensure 4-6 pages per session (including leader notes)

TONE AND STYLE:
- Conversational and pastoral
- Accessible to target audience
- Slightly more formal than a devotional, but not academic
- Theologically sound and pastorally sensitive
- Each session should stand alone but flow as part of the series

Generate the complete study guide now, with all {len(sermons)} sessions."""

    return prompt


async def generate_with_anthropic(prompt: str, model: str) -> str:
    """Generate study guide using Anthropic Claude API"""
    # Set longer timeout for large study guide generation (10 minutes)
    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        timeout=600.0  # 10 minutes
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=16000,
            temperature=1.0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    except Exception as e:
        raise Exception(f"Anthropic API error: {str(e)}")


async def generate_with_openai(prompt: str, model: str) -> str:
    """Generate study guide using OpenAI GPT API"""
    # Set longer timeout for large study guide generation (10 minutes)
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=600.0  # 10 minutes
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert Bible study curriculum designer with deep theological knowledge and pastoral sensitivity."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=16000,
            temperature=1.0
        )

        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"OpenAI API error: {str(e)}")


async def generate_study_guide(
    sermons: list,
    series_title: str,
    target_audience: str,
    model: str
) -> str:
    """
    Generate complete Bible study guide
    Supports multiple AI models with retry logic for partial failures
    """

    # Build the prompt
    prompt = build_generation_prompt(sermons, series_title, target_audience)

    # Map model names to API calls
    model_config = {
        "claude-sonnet-4.5": ("anthropic", "claude-sonnet-4-5-20250929"),
        "claude-3.5-haiku": ("anthropic", "claude-3-5-haiku-20241022"),
        "gpt-4o": ("openai", "gpt-4o")
    }

    if model not in model_config:
        raise ValueError(f"Unknown model: {model}")

    provider, api_model = model_config[model]

    # Attempt generation with retry logic
    max_retries = 1
    attempt = 0

    while attempt <= max_retries:
        try:
            if provider == "anthropic":
                content = await generate_with_anthropic(prompt, api_model)
            elif provider == "openai":
                content = await generate_with_openai(prompt, api_model)
            else:
                raise ValueError(f"Unknown provider: {provider}")

            # Add metadata header
            header = f"""# {series_title}
**Bible Study Guide**

*Generated on {datetime.now().strftime("%B %d, %Y")}*
*Target Audience: {target_audience}*
*Number of Sessions: {len(sermons)}*

---

"""
            return header + content

        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                # Save partial results if any progress was made
                error_content = f"""# {series_title}
**Bible Study Guide - PARTIAL/ERROR**

*Generation failed after {max_retries + 1} attempts*
*Error: {str(e)}*
*Date: {datetime.now().strftime("%B %d, %Y")}*

---

**GENERATION INCOMPLETE**

The study guide generation encountered an error. Please try again or contact support.

Error details: {str(e)}
"""
                return error_content

    return ""

"""
Centralized prompt templates for AI Video Factory
"""

# Default system prompt for visual mapping
VISUAL_MAPPING_SYSTEM = """You are a creative director for vertical video content.
Analyze transcript segments and generate image prompts that visually complement the spoken content.
Your goal is to create high-retention visuals that make the video engaging.

Guidelines:
1. Create vivid, detailed prompts.
2. Avoid any text inside the images (unless specified).
3. Focus on visual metaphors and symbolic representation.
4. Aim for segments of 3-5 seconds each.
5. Ensure the style is consistent throughout the video.

Style Requirements:
{style_hint}

Output Format:
Return a JSON array of objects: 
[{"time": <float: start_time>, "prompt": "<string: detailed_prompt>", "duration": <float: seconds>}]
"""

# Transcription prompt (for Gemini Audio)
TRANSCRIPTION_PROMPT = """Transcribe this audio with accurate timestamps.
Return a JSON array of segments: [{"start": <float>, "end": <float>, "text": "<string>"}]
Only return pure JSON."""

# Dictionary of style-specific modifiers
STYLE_MODIFIERS = {
    "modern": "Use a clean, high-end commercial aesthetic. Minimalist backgrounds, professional lighting.",
    "cyberpunk": "Futuristic, neon-drenched, high contrast. Use blue and purple tones with glowing elements.",
    "animation": "Vibrant 2D character animation style. Bold colors, expressive features, clean lines.",
    "3d_render": "High-quality Octane render, unreal engine 5 style. Soft shadows, realistic textures, cinematic focal depth.",
    "illustration": "Hand-drawn digital illustration. Textured brushes, warm color palette, artistic flair.",
    "motion": "Dynamic motion graphics style. Kinetic typography metaphors, abstract shapes, fast-paced energy.",
    "cinematic": "Hollywood movie look. Anamorphic lens flares, color graded, dramatic lighting.",
}

def get_visual_mapping_prompt(style_hint: str = "modern") -> str:
    """Gets the system prompt with style modifiers applied."""
    modifier = STYLE_MODIFIERS.get(style_hint.lower(), style_hint)
    return VISUAL_MAPPING_SYSTEM.format(style_hint=modifier)

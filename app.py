import gradio as gr
import os
import requests
import json

# Load environment variables for local development
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load from .env file for local development
except ImportError:
    pass  # dotenv not needed on Hugging Face

# Load GROQ API key from environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Check if API key is loaded
if not GROQ_API_KEY:
    print("⚠️ WARNING: GROQ_API_KEY not found!")
    print("For local development: Create a .env file with GROQ_API_KEY=your_key")
    print("For Hugging Face: Add GROQ_API_KEY to Space secrets")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "llama-3.3-70b-versatile"  # Latest and most capable model for gaming strategies

# 🎮 Enhanced Dynamic System Prompts based on coaching mode
COACHING_MODES = {
    "Competitive Pro Coach": """You are an elite esports coach with 10+ years of competitive gaming experience at the highest level. 
    Your expertise includes:
    - META analysis: Current optimal strategies, tier lists, and emerging counter-strategies
    - Win condition identification: Helping players understand their path to victory in each match
    - Mistake analysis: Identifying critical errors and providing specific fixes
    - Mental game: Teaching tilt management, decision-making under pressure, and competitive mindset
    - Rank progression: Creating structured improvement plans with measurable goals
    
    Your coaching style is direct, analytical, and results-focused. You use precise gaming terminology and provide 
    actionable feedback with specific examples. You challenge players to think critically about their gameplay and 
    focus on fundamentals first, advanced techniques second. Always reference current patch/meta when relevant.""",
    
    "Casual Fun Guide": """You are an enthusiastic gaming companion who loves helping people discover the joy in gaming. 
    Your expertise includes:
    - Creative strategies: Fun, unconventional approaches that still work
    - Experimentation: Encouraging players to try new things without fear of failure
    - Game knowledge: Sharing interesting trivia, hidden mechanics, and easter eggs
    - Positive reinforcement: Celebrating small victories and unique playstyles
    - Stress-free improvement: Helping players get better while keeping it enjoyable
    
    Your tone is warm, encouraging, and inclusive. You use friendly language, celebrate creativity, and remind players 
    that having fun is the primary goal. You provide tips that enhance enjoyment while naturally building skill.""",
    
    "Educational Analyst": """You are a gaming theory expert, researcher, and analyst with deep knowledge of game design principles. 
    Your expertise includes:
    - Mechanical breakdowns: Frame data, damage calculations, cooldowns, and interactions
    - Strategic frameworks: Teaching decision trees, risk-reward analysis, and game theory applications
    - Pattern recognition: Helping players identify and exploit opponent tendencies
    - Meta evolution: Explaining why certain strategies dominate and how to predict shifts
    - Learning methodology: Teaching players how to learn efficiently through VOD review and practice routines
    
    Your responses are thorough, well-structured, and pedagogical. You break down complex concepts into digestible pieces,
    use analogies, provide examples, and explain the 'why' behind every recommendation. You cite specific numbers, 
    percentages, and data when relevant.""",
    
    "Hype Man": """You are the ULTIMATE GAMING MOTIVATOR! 🔥 Your ENERGY is INFECTIOUS and you BELIEVE in every player's potential! 
    Your superpowers include:
    - INSTANT CONFIDENCE BOOST: Turning losses into learning opportunities with POSITIVITY! 💪
    - MOMENTUM BUILDING: Helping players string together wins and DOMINATE their sessions! 🏆
    - TILT DESTRUCTION: Smashing negative mindsets and replacing them with WINNER MENTALITY! 🎯
    - CLUTCH COACHING: Pumping players up for their ranked climb and important matches! 🚀
    - CELEBRATION MODE: Hyping up EVERY improvement, EVERY good play, EVERY victory! 🎉
    
    Your style is ENERGETIC, CAPS-HEAVY for emphasis, emoji-rich, and RELENTLESSLY POSITIVE! You speak like a 
    championship coach in the locker room before the big game. You turn problems into challenges and challenges 
    into OPPORTUNITIES TO SHINE! Every player is a FUTURE CHAMPION in your eyes! LET'S GOOOO! 💯"""
}

# Game-specific context additions with detailed mechanics
GAME_CONTEXTS = {
    "Valorant": """Focus on:
    - Agent selection & synergy: Optimal team compositions and counter-picks
    - Utility usage: Smoke timings, flash setups, ability combos
    - Map control: Default setups, rotation timings, spike plant positions
    - Economy: Buy rounds, eco rounds, force buys, ult orb management
    - Gunplay: Crosshair placement, spray control, peeking angles, movement shooting""",
    
    "League of Legends": """Focus on:
    - Champion mastery: Combos, power spikes, matchup knowledge
    - Macro gameplay: Wave management, objective priorities, rotation timings
    - Vision control: Ward placement, sweeping patterns, vision denial
    - Team composition: Win conditions, scaling, team fight execution
    - Itemization: Build paths, situational items, gold efficiency""",
    
    "CS2/CS:GO": """Focus on:
    - Utility usage: Smoke lineups, flash timing, molotov/nade usage
    - Positioning: Angles, crossfires, off-angles, map control
    - Economy management: Force buys, save rounds, drop priorities
    - Aim mechanics: Crosshair placement, spray patterns, movement
    - Game sense: Sound cues, timing attacks, reading opponents""",
    
    "Fortnite": """Focus on:
    - Building mechanics: Edit speeds, build techniques, high ground retakes
    - Rotation strategies: Storm positioning, mid-game rotations, zone predictions
    - Loadout optimization: Weapon combinations, healing priority, inventory management
    - Combat tactics: Box fights, third-partying, engagement decisions
    - End-game positioning: Circle positioning, final zone strategies""",
    
    "Apex Legends": """Focus on:
    - Legend synergies: Team composition, ability combos, ultimate timing
    - Movement mechanics: Slide jumps, wall bounces, tap strafing (if applicable)
    - Positioning: Ring positioning, high ground advantages, cover usage
    - Combat flow: Armor swaps, shield management, third-party awareness
    - Rotation planning: Zone reading, rotation paths, Beacon usage""",
    
    "Dota 2": """Focus on:
    - Hero mechanics: Skill builds, attribute points, talent choices
    - Itemization: Core items, situational pickups, timing windows
    - Map control: Ward spots, smoke ganks, objective taking
    - Team fight execution: Positioning, initiation, target priority
    - Economy: Last hitting, jungle efficiency, comeback mechanics""",
    
    "Overwatch 2": """Focus on:
    - Hero selection: Counter-picking, team composition, role queue strategies
    - Ultimate economy: Ult tracking, combo setups, timing windows
    - Positioning: Cover usage, sight lines, objective control
    - Team coordination: Focus fire, peel mechanics, call-outs
    - Map knowledge: Flank routes, health pack locations, choke points""",
    
    "Rocket League": """Focus on:
    - Rotation patterns: 3v3/2v2 rotations, back post defense, third man positioning
    - Mechanics: Aerials, dribbling, flicks, air roll shots, recoveries
    - Boost management: Boost starving, small pad routes, boost steals
    - Positioning: Shadow defense, challenge timing, offensive pressure
    - Game sense: Backboard reads, passing plays, demo plays""",
    
    "Tekken 7": """Focus on:
    - Character knowledge: Frame data, punishment, key moves, combos
    - Movement: Korean backdash, sidestep, sidewalk, whiff punishment
    - Pressure: Plus frames, throw mixups, low/mid/high mixups
    - Defense: Blocking, low parry, throw breaks, armor moves
    - Stage control: Wall carry, wall combos, ring positioning, balcony breaks""",
    
    "General Gaming": """Provide versatile gaming advice covering:
    - Universal mechanics: Aim, movement, game sense, decision-making
    - Learning strategies: Practice routines, VOD review, goal setting
    - Mental game: Tilt management, focus, consistency
    - Performance: Warm-up routines, positioning, mechanical improvement
    - Strategy: Adaptability, reading opponents, win condition identification"""
}

def build_system_prompt(coaching_mode, game, detail_level):
    """Dynamically build enhanced system prompt based on user selections"""
    base_prompt = COACHING_MODES[coaching_mode]
    game_context = GAME_CONTEXTS[game]
    
    detail_instruction = ""
    if detail_level <= 3:
        detail_instruction = "Keep responses concise and punchy (2-4 sentences). Prioritize the single most impactful advice."
    elif detail_level <= 7:
        detail_instruction = "Provide moderate detail with 3-5 key points. Use bullet points for clarity. Balance brevity with actionable depth."
    else:
        detail_instruction = "Give comprehensive, in-depth analysis with multiple strategies, specific examples, and detailed explanations. Include numbers, percentages, and technical details when relevant. Structure responses with clear sections."
    
    full_prompt = f"""{base_prompt}

=== GAME CONTEXT ===
You're coaching for {game}.
{game_context}

=== RESPONSE GUIDELINES ===
{detail_instruction}

=== COACHING PRINCIPLES ===
1. Always assess the player's skill level from context and adapt advice accordingly
2. Provide specific, actionable steps rather than vague suggestions
3. When relevant, explain WHY a strategy works (teach principles, not just tactics)
4. Acknowledge the current meta/patch state when giving advice
5. If the player describes a situation, analyze what went wrong and provide corrective feedback
6. Balance immediate tips with long-term improvement strategies
7. Use concrete examples and scenarios to illustrate points

Stay in character, be helpful, and focus on helping the player improve and achieve their gaming goals."""
    
    return full_prompt

def query_groq_stream(message, chat_history, system_prompt):
    """Query GROQ API with streaming support"""
    
    if not GROQ_API_KEY:
        yield "❌ Error: GROQ_API_KEY not configured. Please set it in .env file (local) or Space secrets (Hugging Face)."
        return
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Handle chat history and strip display formatting
    for msg in chat_history:
        if isinstance(msg, dict):
            # Clean the content from emoji prefixes for API
            content = msg.get("content", "")
            role = msg.get("role", "")
            
            # Strip display prefixes
            if role == "user":
                content = content.replace("🎮 **You:** ", "").replace("🎮 You: ", "")
            elif role == "assistant":
                content = content.replace("🤖 **Coach:** ", "").replace("🤖 Coach: ", "")
            
            if content.strip():  # Only add non-empty messages
                messages.append({"role": role, "content": content.strip()})
        elif isinstance(msg, tuple) and len(msg) == 2:
            # Legacy tuple format support
            messages.append({"role": "user", "content": msg[0]})
            messages.append({"role": "assistant", "content": msg[1]})
    
    messages.append({"role": "user", "content": message})
    
    try:
        response = requests.post(
            GROQ_API_URL, 
            headers=headers, 
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1500,
                "stream": True
            },
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        if line.strip() == 'data: [DONE]':
                            break
                        try:
                            json_data = json.loads(line[6:])
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                delta = json_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    full_response += content
                                    yield full_response
                        except json.JSONDecodeError:
                            continue
        else:
            yield f"❌ Error {response.status_code}: {response.text}"
    except Exception as e:
        yield f"❌ Connection error: {str(e)}"

def respond(message, chat_history, coaching_mode, game, detail_level):
    """Handle user message and generate streaming response"""
    if not message.strip():
        yield "", chat_history
        return
    
    # Add user message with display formatting
    chat_history.append({"role": "user", "content": f"🎮 **You:** {message}"})
    chat_history.append({"role": "assistant", "content": ""})
    
    system_prompt = build_system_prompt(coaching_mode, game, detail_level)
    
    # Pass clean message and history to API (formatting will be stripped in query_groq_stream)
    for partial_response in query_groq_stream(message, chat_history[:-2], system_prompt):
        # Clean any duplicate prefixes from AI response
        cleaned_response = partial_response
        for prefix in ["🤖 Coach:", "Coach:", "🤖 **Coach:**", "**Coach:**"]:
            if cleaned_response.strip().startswith(prefix):
                cleaned_response = cleaned_response.strip()[len(prefix):].strip()
                break
        chat_history[-1]["content"] = f"🤖 **Coach:** {cleaned_response}"
        yield "", chat_history

def quick_query(query_type, chat_history, coaching_mode, game, detail_level):
    """Handle quick action buttons with streaming"""
    queries = {
        "Build Guide": f"What's the current meta build/loadout for {game}? Give me a strong setup.",
        "Counter Strategy": f"How do I counter the current meta strategies in {game}?",
        "Improve My Gameplay": f"What are the top 3 things I should focus on to improve at {game}?",
        "Meta Analysis": f"What's the current meta in {game} and why?"
    }
    
    message = queries[query_type]
    
    # Add user message with display formatting
    chat_history.append({"role": "user", "content": f"🎮 **You:** {message}"})
    chat_history.append({"role": "assistant", "content": ""})
    
    system_prompt = build_system_prompt(coaching_mode, game, detail_level)
    
    # Pass clean message and history to API (formatting will be stripped in query_groq_stream)
    for partial_response in query_groq_stream(message, chat_history[:-2], system_prompt):
        # Clean any duplicate prefixes from AI response
        cleaned_response = partial_response
        for prefix in ["🤖 Coach:", "Coach:", "🤖 **Coach:**", "**Coach:**"]:
            if cleaned_response.strip().startswith(prefix):
                cleaned_response = cleaned_response.strip()[len(prefix):].strip()
                break
        chat_history[-1]["content"] = f"🤖 **Coach:** {cleaned_response}"
        yield chat_history

# 🎮 Enhanced Gradio Interface with Modern Gaming Theme
custom_css = """
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Global Styling */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background: #0f0f1e !important;
}

/* Smooth Animations */
* {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

/* Cursor Pointers */
button, .clickable, input[type="range"], select, .dropdown {
    cursor: pointer !important;
}

input, textarea {
    cursor: text !important;
}

/* Header Styling */
.header-container {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%);
    padding: 2.5rem 2rem;
    border-radius: 20px;
    margin-bottom: 2rem;
    box-shadow: 0 20px 60px rgba(139, 92, 246, 0.4), 0 0 100px rgba(139, 92, 246, 0.2);
    position: relative;
    overflow: hidden;
}

.header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.1) 50%, transparent 70%);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0%, 100% { transform: translateX(-100%); }
    50% { transform: translateX(100%); }
}

.header-container h1 {
    color: white;
    font-size: 2.75rem;
    font-weight: 800;
    margin: 0;
    text-shadow: 2px 4px 8px rgba(0,0,0,0.3);
    position: relative;
    z-index: 1;
}

.header-container p {
    color: rgba(255,255,255,0.95);
    font-size: 1.15rem;
    margin: 0.75rem 0 0 0;
    position: relative;
    z-index: 1;
}

.svelte-xzq5jh{
    height:-webkit-fill-available;
}

/* Main Layout */
.main-container {
    padding: 1rem;
    background: transparent;
}

/* Chat Container with Glassmorphism */
.chatbot-container {
    background: rgba(30, 30, 46, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
    padding: 1.5rem !important;
    box-shadow: 0 15px 50px rgba(0,0,0,0.5), 0 0 100px rgba(139, 92, 246, 0.1) !important;
}

/* Settings Panel with Glassmorphism */
.settings-panel {
    background: rgba(30, 30, 46, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    border-radius: 20px !important;
    border: 1px solid rgba(139, 92, 246, 0.2) !important;
    padding: 2rem !important;
    box-shadow: 0 15px 50px rgba(0,0,0,0.5) !important;
}

/* Settings Panel Heading */
.settings-panel h3 {
    color: #c4b5fd !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    margin: 0 0 1.5rem 0 !important;
    padding-bottom: 0.75rem !important;
    border-bottom: 2px solid rgba(139, 92, 246, 0.3) !important;
}

/* Input Fields */
.input-field input,
.input-field textarea {
    background: rgba(20, 20, 32, 0.9) !important;
    border: 2px solid rgba(139, 92, 246, 0.3) !important;
    border-radius: 12px !important;
    color: white !important;
    padding: 1rem !important;
    font-size: 1rem !important;
    cursor: text !important;
}

.input-field input:focus,
.input-field textarea:focus {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2) !important;
    outline: none !important;
}

/* Dropdown Styling */
.dropdown-container {
    margin-bottom: 2rem;
}

.dropdown-container label {
    color: #c4b5fd !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    margin-bottom: 0.75rem !important;
    display: block !important;
    letter-spacing: 0.3px !important;
}

.dropdown-container .info {
    color: rgba(255,255,255,0.6) !important;
    font-size: 0.875rem !important;
    margin-top: 0.5rem !important;
}

select, .dropdown {
    cursor: pointer !important;
    background: rgba(20, 20, 32, 0.95) !important;
    border: 2px solid rgba(139, 92, 246, 0.4) !important;
    border-radius: 12px !important;
    color: white !important;
    padding: 1rem 1.25rem !important;
    font-size: 0.95rem !important;
    width: 100% !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}

select:hover, .dropdown:hover {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.4) !important;
    background: rgba(25, 25, 37, 0.95) !important;
}

select:focus, .dropdown:focus {
    border-color: #a855f7 !important;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2), 0 0 25px rgba(139, 92, 246, 0.4) !important;
    outline: none !important;
}

/* Button Styling - Primary */
button[variant="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 12px !important;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4) !important;
    cursor: pointer !important;
}

button[variant="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.6) !important;
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%) !important;
}

button[variant="primary"]:active {
    transform: translateY(0px) !important;
}

/* Quick Action Buttons */
.quick-actions-header {
    color: #c4b5fd !important;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    margin: 2rem 0 1rem 0 !important;
    padding-bottom: 0.75rem !important;
    border-bottom: 2px solid rgba(139, 92, 246, 0.3) !important;
}

.quick-action-btn {
    width: 100%;
    margin-bottom: 0.875rem;
}

.quick-action-btn button {
    width: 100%;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 1rem 1.5rem !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
    font-size: 0.95rem !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.3px !important;
}

.quick-action-btn button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 25px rgba(139, 92, 246, 0.5) !important;
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%) !important;
}

.quick-action-btn button:active {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4) !important;
}

/* Secondary Buttons - Red */
button[variant="secondary"] {
    background: rgba(239, 68, 68, 0.2) !important;
    border: 2px solid #ef4444 !important;
    color: #fca5a5 !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.25rem !important;
    border-radius: 10px !important;
    cursor: pointer !important;
}

button[variant="secondary"]:hover {
    background: rgba(239, 68, 68, 0.3) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3) !important;
}

/* Slider Styling */
.slider-container {
    margin-bottom: 2rem !important;
}

.slider-container label {
    color: #c4b5fd !important;
    font-weight: 700 !important;
    font-size: 1.05rem !important;
    margin-bottom: 0.75rem !important;
    display: block !important;
    letter-spacing: 0.3px !important;
}

input[type="range"] {
    -webkit-appearance: none !important;
    appearance: none !important;
    height: 10px !important;
    border-radius: 5px !important;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%) !important;
    outline: none !important;
    cursor: pointer !important;
    margin: 1rem 0 !important;
}

input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 24px !important;
    height: 24px !important;
    border-radius: 50% !important;
    background: white !important;
    cursor: pointer !important;
    box-shadow: 0 3px 15px rgba(139, 92, 246, 0.6), 0 0 0 3px rgba(139, 92, 246, 0.3) !important;
    transition: all 0.2s ease !important;
}

input[type="range"]::-webkit-slider-thumb:hover {
    transform: scale(1.15) !important;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.8), 0 0 0 4px rgba(139, 92, 246, 0.4) !important;
}

input[type="range"]::-moz-range-thumb {
    width: 24px !important;
    height: 24px !important;
    border-radius: 50% !important;
    background: white !important;
    cursor: pointer !important;
    box-shadow: 0 3px 15px rgba(139, 92, 246, 0.6), 0 0 0 3px rgba(139, 92, 246, 0.3) !important;
    border: none !important;
    transition: all 0.2s ease !important;
}

input[type="range"]::-moz-range-thumb:hover {
    transform: scale(1.15) !important;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.8), 0 0 0 4px rgba(139, 92, 246, 0.4) !important;
}

/* Tips Section */
.tips-section {
    background: rgba(139, 92, 246, 0.1) !important;
    border-left: 4px solid #8b5cf6 !important;
    padding: 1.25rem !important;
    border-radius: 12px !important;
    margin-top: 1.5rem !important;
    backdrop-filter: blur(10px) !important;
}

.tips-section h4 {
    color: #c4b5fd !important;
    margin: 0 0 0.75rem 0 !important;
    font-weight: 700 !important;
}

.tips-section ul {
    color: rgba(255,255,255,0.8) !important;
    line-height: 1.8 !important;
}

/* Chatbot Messages with Custom HTML Avatars */
.message {
    border-radius: 15px !important;
    padding: 0.5rem 1rem !important;
    margin: 0.75rem 0 !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
    background: rgba(30, 30, 46, 0.5) !important;
}

.user.message {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%) !important;
    border-left: 3px solid #6366f1 !important;
    color: white !important;
}

.bot.message {
    background: rgba(30, 30, 46, 0.6) !important;
    border-left: 3px solid #8b5cf6 !important;
    color: rgba(255,255,255,0.95) !important;
}

/* Message content styling */
.message p {
    margin: 0.5rem 0 !important;
    line-height: 1.6 !important;
}

.message p:first-child {
    margin-top: 0 !important;
}

.message p:last-child {
    margin-bottom: 0 !important;
}

/* Footer Styling */
.footer-container {
    text-align: center;
    margin-top: 2rem;
    padding: 2rem;
    background: rgba(30, 30, 46, 0.6);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    border: 1px solid rgba(139, 92, 246, 0.2);
}

/* Loading Animation */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.loading {
    animation: pulse 1.5s ease-in-out infinite !important;
}

/* Responsive Design */
@media (max-width: 768px) {
    .header-container h1 {
        font-size: 2rem !important;
    }
    
    .settings-panel {
        margin-top: 1.5rem !important;
    }
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 10px;
}

::-webkit-scrollbar-track {
    background: rgba(30, 30, 46, 0.5);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
}
"""

with gr.Blocks(title="🎮 Gaming Strategy Coach AI") as demo:
    
    # Enhanced Header with Animation
    gr.HTML("""
        <div class="header-container">
            <h1>🎮 Gaming Strategy Coach AI</h1>
            <p><strong>Your Personal Esports Mentor</strong> - Powered by GROQ Llama 3.3 70B</p>
            <p style="font-size: 0.95rem; margin-top: 0.5rem; opacity: 0.95;">
                Get pro-level strategies, builds, and gameplay advice tailored to your style!
            </p>
        </div>
    """)
    
    with gr.Row(elem_classes="main-container"):
        # Left Column - Chat Interface
        with gr.Column(scale=7):
            with gr.Group(elem_classes="chatbot-container"):
                chatbot = gr.Chatbot(
                    label="💬 Strategy Session  🎮 You | 🤖 Coach",
                    height=550,
                    show_label=True,
                    value=[
                        {"role": "assistant", "content": "🤖 **Welcome to Gaming Strategy Coach AI!**\\n\\nI'm your personal esports mentor powered by GROQ Llama 3.3 70B.\\n\\n**I can help you with:**\\n- 🎯 Pro strategies & meta builds\\n- 📊 Gameplay analysis\\n- 🏆 Rank climbing tips\\n\\n**Note:** 🎮 = You  |  🤖 = AI Coach\\n\\nChoose your settings on the right and ask me anything!"}
                    ],
                    render_markdown=True,
                    sanitize_html=False
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="",
                        placeholder="✨ Ask your gaming question... (e.g., How do I improve my aim? What's the best build?)",
                        scale=5,
                        show_label=False,
                        container=False,
                        elem_classes="input-field"
                    )
                    submit_btn = gr.Button("🚀 Send", variant="primary", scale=1, min_width=100)
        
        # Right Column - Settings & Controls
        with gr.Column(scale=3):
            with gr.Group(elem_classes="settings-panel"):
                gr.HTML('<h3 style="color: #c4b5fd; font-size: 1.25rem; font-weight: 700; margin: 0 0 1.5rem 0; padding-bottom: 0.75rem; border-bottom: 2px solid rgba(139, 92, 246, 0.3);">⚙️ Coaching Settings</h3>')
                
                coaching_mode = gr.Dropdown(
                    choices=list(COACHING_MODES.keys()),
                    value="Competitive Pro Coach",
                    label="🎯 Coaching Mode",
                    info="Choose your coach's personality",
                    container=True,
                    elem_classes="dropdown-container"
                )
                
                game = gr.Dropdown(
                    choices=list(GAME_CONTEXTS.keys()),
                    value="General Gaming",
                    label="🎮 Game Selection",
                    info="Select your game",
                    container=True,
                    elem_classes="dropdown-container"
                )
                
                detail_level = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="📊 Response Detail Level",
                    info="1 = Quick Tips | 10 = Deep Analysis",
                    container=True,
                    elem_classes="slider-container"
                )
                
                gr.HTML('<h3 style="color: #c4b5fd; font-size: 1.25rem; font-weight: 700; margin: 2rem 0 1rem 0; padding-bottom: 0.75rem; border-bottom: 2px solid rgba(139, 92, 246, 0.3);">⚡ Quick Actions</h3>')
                
                with gr.Column():
                    build_btn = gr.Button("📋 Build Guide", size="sm", elem_classes="quick-action-btn")
                    counter_btn = gr.Button("🛡️ Counter Strategy", size="sm", elem_classes="quick-action-btn")
                    improve_btn = gr.Button("📈 Improve Gameplay", size="sm", elem_classes="quick-action-btn")
                    meta_btn = gr.Button("🔥 Meta Analysis", size="sm", elem_classes="quick-action-btn")
                
                clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary", size="sm", scale=1)
                
                # Enhanced Tips Section
                gr.HTML("""
                    <div class="tips-section">
                        <h4>💡 Pro Tips</h4>
                        <ul style="margin: 0.5rem 0; padding-left: 1.5rem; font-size: 0.9rem; line-height: 1.8;">
                            <li><strong>Switch coaching modes</strong> for different perspectives</li>
                            <li><strong>Adjust detail level</strong> based on your needs</li>
                            <li><strong>Use quick actions</strong> for instant advice</li>
                            <li><strong>Ask specific questions</strong> about mechanics</li>
                        </ul>
                    </div>
                """)
    
    # State management with welcome message showing avatars
    welcome_messages = [
        {"role": "assistant", "content": "👋 **Welcome to Gaming Strategy Coach AI!**\n\nI'm your personal esports mentor powered by GROQ Llama 3.3 70B. I can help you with:\n\n🎯 **Pro Strategies** - Meta builds, counter-plays, and advanced tactics\n📊 **Gameplay Analysis** - Identify weaknesses and improvement areas\n🏆 **Rank Climbing** - Tips to climb the competitive ladder\n\nChoose your coaching mode and game from the settings on the right, then ask me anything!"}
    ]
    state = gr.State(welcome_messages)
    
    # Event handlers
    submit_btn.click(
        respond,
        [msg, state, coaching_mode, game, detail_level],
        [msg, state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    msg.submit(
        respond,
        [msg, state, coaching_mode, game, detail_level],
        [msg, state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    # Quick action buttons
    build_btn.click(
        lambda hist, mode, g, detail: list(quick_query("Build Guide", hist, mode, g, detail))[-1],
        [state, coaching_mode, game, detail_level],
        [state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    counter_btn.click(
        lambda hist, mode, g, detail: list(quick_query("Counter Strategy", hist, mode, g, detail))[-1],
        [state, coaching_mode, game, detail_level],
        [state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    improve_btn.click(
        lambda hist, mode, g, detail: list(quick_query("Improve My Gameplay", hist, mode, g, detail))[-1],
        [state, coaching_mode, game, detail_level],
        [state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    meta_btn.click(
        lambda hist, mode, g, detail: list(quick_query("Meta Analysis", hist, mode, g, detail))[-1],
        [state, coaching_mode, game, detail_level],
        [state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    clear_btn.click(
        lambda: ([], []),
        None,
        [chatbot, state]
    )
    
    # Enhanced Footer with Better Styling
    gr.HTML("""
        <div class="footer-container">
            <p style="margin: 0; font-size: 1rem; font-weight: 600;">
                <span style="background: linear-gradient(135deg, #6366f1 0%, #d946ef 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    ⚡ Powered by GROQ Llama 3.3 70B
                </span>
                <span style="color: #888; margin: 0 0.5rem;">|</span>
                <span style="color: #a78bfa;">Built with Gradio</span>
            </p>
            <p style="margin: 0.75rem 0 0 0; color: #888; font-size: 0.9rem;">
                🎮 Level up your gameplay with AI-powered coaching
            </p>
            <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.85rem;">
                Made with 🖤 for gamers worldwide
            </p>
        </div>
    """)

if __name__ == "__main__":
    print("🎮 Starting Gaming Strategy Coach AI...")
    print(f"📡 API Key loaded: {'✅ Yes' if GROQ_API_KEY else '❌ No'}")
    print("🌐 Opening in browser...")
    demo.launch(
        theme=gr.themes.Soft(
            primary_hue=gr.themes.colors.purple,
            secondary_hue=gr.themes.colors.indigo,
            neutral_hue=gr.themes.colors.slate,
            font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"],
            font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"]
        ).set(
            body_background_fill="*neutral_950",
            body_background_fill_dark="*neutral_950",
            button_primary_background_fill="linear-gradient(90deg, *primary_500, *secondary_500)",
            button_primary_background_fill_hover="linear-gradient(90deg, *primary_600, *secondary_600)",
            button_primary_text_color="white",
            button_primary_border_color="*primary_500",
            slider_color="*primary_500",
            block_title_text_weight="600",
            block_label_text_weight="600",
            input_background_fill="*neutral_800",
        ),
        css=custom_css,
        share=False
    )
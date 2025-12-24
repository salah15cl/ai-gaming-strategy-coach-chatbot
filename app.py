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

# 🎮 Dynamic System Prompts based on coaching mode
COACHING_MODES = {
    "Competitive Pro Coach": """You are an elite esports coach with years of competitive gaming experience. 
    You focus on META strategies, optimal builds, rank climbing tactics, and competitive mindset. 
    Your responses are direct, strategic, and aimed at winning. You analyze plays critically and provide 
    actionable advice for improvement. Use gaming terminology confidently.""",
    
    "Casual Fun Guide": """You are a friendly gaming buddy who loves helping people enjoy games more. 
    You focus on fun strategies, creative plays, and enjoying the gaming experience. Your tone is relaxed, 
    encouraging, and you celebrate unique playstyles. You balance improvement with enjoyment.""",
    
    "Educational Analyst": """You are a gaming theory expert and analyst. You provide deep explanations 
    of game mechanics, mathematical analysis of builds, psychological aspects of gameplay, and detailed 
    breakdowns of strategies. Your responses are thorough, well-structured, and educational.""",
    
    "Hype Man": """You are an energetic motivational gaming coach! You pump players up, boost their 
    confidence, and help them overcome tilt. Your responses are enthusiastic, positive, and motivating. 
    You use emojis, caps for emphasis, and always believe in the player's potential! LET'S GO! 🔥"""
}

# Game-specific context additions
GAME_CONTEXTS = {
    "Valorant": "Focus on agent abilities, map control, economy management, and tactical positioning.",
    "League of Legends": "Focus on champion mechanics, macro gameplay, objectives, and team composition.",
    "CS2/CS:GO": "Focus on utility usage, positioning, economy, crosshair placement, and map knowledge.",
    "Fortnite": "Focus on building techniques, rotation strategies, loadout optimization, and positioning.",
    "Apex Legends": "Focus on legend synergies, movement mechanics, positioning, and team coordination.",
    "Dota 2": "Focus on hero mechanics, itemization, map control, and team fight execution.",
    "Overwatch 2": "Focus on hero counters, ultimate economy, team composition, and positioning.",
    "Rocket League": "Focus on rotation, mechanics, boost management, and positioning.",
    "General Gaming": "Provide versatile gaming advice applicable across multiple titles."
}

def build_system_prompt(coaching_mode, game, detail_level):
    """Dynamically build system prompt based on user selections"""
    base_prompt = COACHING_MODES[coaching_mode]
    game_context = GAME_CONTEXTS[game]
    
    detail_instruction = ""
    if detail_level <= 3:
        detail_instruction = "Keep responses concise and to the point (2-3 sentences)."
    elif detail_level <= 7:
        detail_instruction = "Provide moderate detail with key points (1 paragraph)."
    else:
        detail_instruction = "Give comprehensive analysis with examples and multiple strategies (detailed response)."
    
    full_prompt = f"""{base_prompt}

Game Context: You're coaching for {game}. {game_context}

Response Style: {detail_instruction}

Always be helpful, accurate, and adapt your advice to the player's skill level when mentioned."""
    
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
    
    # Handle chat history in Gradio's message format
    for msg in chat_history:
        if isinstance(msg, dict):
            messages.append(msg)
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
    
    # Add user message immediately
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": ""})
    
    system_prompt = build_system_prompt(coaching_mode, game, detail_level)
    
    # Stream the response
    for partial_response in query_groq_stream(message, chat_history[:-1], system_prompt):
        chat_history[-1]["content"] = partial_response
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
    
    # Add user message immediately
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": ""})
    
    system_prompt = build_system_prompt(coaching_mode, game, detail_level)
    
    # Stream the response
    for partial_response in query_groq_stream(message, chat_history[:-1], system_prompt):
        chat_history[-1]["content"] = partial_response
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
    padding: 1.5rem !important;
    box-shadow: 0 15px 50px rgba(0,0,0,0.5) !important;
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
    margin-bottom: 1.5rem;
}

.dropdown-container label {
    color: rgba(255,255,255,0.95) !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    margin-bottom: 0.75rem !important;
    display: block !important;
}

select, .dropdown {
    cursor: pointer !important;
    background: rgba(20, 20, 32, 0.95) !important;
    border: 2px solid rgba(139, 92, 246, 0.4) !important;
    border-radius: 10px !important;
    color: white !important;
    padding: 0.875rem !important;
    font-size: 0.95rem !important;
    width: 100% !important;
}

select:hover, .dropdown:hover {
    border-color: #8b5cf6 !important;
    box-shadow: 0 0 15px rgba(139, 92, 246, 0.3) !important;
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
.quick-action-btn {
    width: 100%;
    margin-bottom: 0.75rem;
}

.quick-action-btn button {
    width: 100%;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.875rem 1.25rem !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
    font-size: 0.95rem !important;
    cursor: pointer !important;
}

.quick-action-btn button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5) !important;
    background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%) !important;
}

.quick-action-btn button:active {
    transform: translateY(0px) !important;
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
input[type="range"] {
    -webkit-appearance: none !important;
    appearance: none !important;
    height: 8px !important;
    border-radius: 5px !important;
    background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 50%, #d946ef 100%) !important;
    outline: none !important;
    cursor: pointer !important;
}

input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 20px !important;
    height: 20px !important;
    border-radius: 50% !important;
    background: white !important;
    cursor: pointer !important;
    box-shadow: 0 2px 10px rgba(139, 92, 246, 0.5) !important;
}

input[type="range"]::-moz-range-thumb {
    width: 20px !important;
    height: 20px !important;
    border-radius: 50% !important;
    background: white !important;
    cursor: pointer !important;
    box-shadow: 0 2px 10px rgba(139, 92, 246, 0.5) !important;
    border: none !important;
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

/* Chatbot Messages */
.message {
    border-radius: 15px !important;
    padding: 1rem 1.25rem !important;
    margin: 0.5rem 0 !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
}

.user.message {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
}

.bot.message {
    background: rgba(30, 30, 46, 0.9) !important;
    border: 1px solid rgba(139, 92, 246, 0.3) !important;
    color: rgba(255,255,255,0.95) !important;
}

/* Message avatars */
.avatar-container {
    display: flex !important;
    align-items: center !important;
    margin-right: 0.75rem !important;
}

.avatar-container img {
    width: 32px !important;
    height: 32px !important;
    border-radius: 50% !important;
    display: block !important;
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
                    label="💬 Strategy Session",
                    height=550,
                    show_label=True,
                    avatar_images=("🎮", "🤖"),
                    placeholder="👋 Welcome! Ask me anything about gaming strategies, builds, or gameplay tips!"
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
                gr.Markdown("### ⚙️ Coaching Settings")
                
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
                    container=True
                )
                
                gr.Markdown("### ⚡ Quick Actions")
                
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
    
    # State management
    state = gr.State([])
    
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
        lambda hist, mode, g, detail: quick_query("Build Guide", hist, mode, g, detail),
        [state, coaching_mode, game, detail_level],
        [state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    counter_btn.click(
        lambda hist, mode, g, detail: quick_query("Counter Strategy", hist, mode, g, detail),
        [state, coaching_mode, game, detail_level],
        [state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    improve_btn.click(
        lambda hist, mode, g, detail: quick_query("Improve My Gameplay", hist, mode, g, detail),
        [state, coaching_mode, game, detail_level],
        [state]
    ).then(
        lambda hist: hist,
        [state],
        [chatbot]
    )
    
    meta_btn.click(
        lambda hist, mode, g, detail: quick_query("Meta Analysis", hist, mode, g, detail),
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
                Made with ❤️ for gamers worldwide
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
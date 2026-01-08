import streamlit as st
import json
import difflib
import html

# --- CSS & Styling ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* Global Font & Colors */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
        
        :root {
            --primary-color: #6366f1; /* Indigo */
            --primary-light: #e0e7ff;
            --secondary-color: #ec4899; /* Pink */
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #1e293b;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
        }

        .stApp {
            background-color: var(--bg-color);
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
        }
        
        /* Headers */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            color: var(--text-main);
            letter-spacing: -0.025em;
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid var(--border-color);
            box-shadow: 1px 0 4px rgba(0,0,0,0.02);
        }
        
        /* Buttons - Modern & Premium */
        div.stButton > button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            border: 1px solid var(--border-color);
        }
        
        div.stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        /* Primary Action Buttons */
        div.stButton > button[kind="primary"], div.stButton > button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white !important;
            border: none;
            font-weight: 600;
        }
        
        /* Cards */
        .stContainer, div[data-testid="stExpander"] {
            background: var(--card-bg);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        }
        
        /* Metrics */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            font-weight: 700;
            background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        /* Data Editor */
        div[data-testid="stDataEditor"] {
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }

        /* Diff View Styling */
        .diff-container { 
            display: flex; 
            gap: 12px; 
            width: 100%; 
            /* Let parent or page handle scroll */
            overflow-x: auto;
            padding-bottom: 8px; 
            position: relative;
        }
        .diff-column {
            flex: 1;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            background: white;
            min-width: 350px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
            /* Allow full height for shared scrolling */
            height: fit-content;
        }
        .diff-header {
            padding: 12px;
            background: #f1f5f9;
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
            color: var(--text-main);
            /* Sticky Header */
            position: sticky; 
            top: 0;
            z-index: 100;
            text-align: center;
        }
        .diff-content {
            padding: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            line-height: 1.5;
            white-space: pre-wrap;
            /* Remove individual scroll */
            overflow: visible;
            color: #334155;
        }
        .diff-line { display: block; padding: 0 4px; min-height: 1.5em; }
        .diff-add { background-color: #dcfce7; color: #15803d; } /* Green for Add (though typically add/del depends on perspective) */
        .diff-del { background-color: #fee2e2; color: #b91c1c; } /* Red for Del */
        .diff-change { background-color: #fee2e2; color: #b91c1c; } /* Red for Change (Requested: different = red) */
        .diff-same { background-color: #dcfce7; color: #15803d; } /* Green for Same (Requested: same = green) */
        .diff-details { background-color: #f8fafc; border: 1px dashed #cbd5e1; margin: 4px 0; border-radius: 4px; }
        .diff-summary { cursor: pointer; color: #64748b; font-size: 11px; padding: 4px; font-style: italic; }

        /* Sidebar Navigation Styling */
        section[data-testid="stSidebar"] {
            background-color: #ffffff;
            border-right: 1px solid var(--border-color);
        }

        /* Sidebar Header */
        section[data-testid="stSidebar"] h1 {
            background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1.8rem;
            padding-bottom: 1rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--border-color);
        }

        /* Sidebar Styling Refined */
        /* Target the generic class for robustness */
        div.stRadio [role="radiogroup"] {
            gap: 8px;
        }

        /* The Label (The clickable tap area) */
        div.stRadio [role="radiogroup"] label {
             background-color: transparent !important;
             padding: 12px 16px !important;
             border-radius: 8px !important;
             margin-bottom: 4px !important;
             width: 100%;
             transition: all 0.2s ease;
             cursor: pointer;
             display: flex !important; 
             align-items: center;
        }
        
        div.stRadio [role="radiogroup"] label:hover {
             background-color: #f1f5f9 !important;
        }

        /* Selected State */
        div.stRadio [role="radiogroup"] label:has(input:checked) {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
            color: white !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        div.stRadio [role="radiogroup"] label:has(input:checked) * {
            color: white !important;
        }

        /* Hide the Radio Circle and Input */
        div.stRadio [role="radiogroup"] input {
             position: absolute;
             opacity: 0;
             width: 0;
             height: 0;
        }
        
        /* The circle is usually the first <div> child of the label, or inside it */
        div.stRadio [role="radiogroup"] label > div:first-child {
            display: none !important;
        }
        
        /* Ensure the text has no weird margins */
        div.stRadio [role="radiogroup"] label > div[data-testid="stMarkdownContainer"] {
            margin: 0 !important;
        }

    </style>
    """, unsafe_allow_html=True)

# --- Visual Diff Helper ---
import streamlit as st

@st.cache_data(show_spinner=False)
def generate_side_by_side_html(data_list):
    """
    Generates HTML for side-by-side comparison with Unified Folding.
    data_list: List of dicts [{'name': 'Env Name', 'content': json_obj}]
    """
    if not data_list:
        return '<div style="color: #64748b; font-style: italic; padding: 20px;">No comparison data available.</div>'

    json_strs = []
    for item in data_list:
        s = json.dumps(item['content'], indent=2, ensure_ascii=False, sort_keys=True)
        json_strs.append(s.splitlines())
        
    cols_html = ""
    ref_lines = json_strs[0]
    
    # 1. Calculate Global Safe-to-Fold Mask on Reference
    # A line in Ref is safe to fold if it is identical in ALL targets.
    # We use difflib to find 'equal' blocks for each target.
    # Initialize mask as True (Safe)
    safe_mask = [True] * len(ref_lines)
    
    for i in range(1, len(json_strs)):
        target_lines = json_strs[i]
        matcher = difflib.SequenceMatcher(None, ref_lines, target_lines)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                # Mark these Ref lines as Unsafe (changed in this target)
                for k in range(i1, i2):
                    safe_mask[k] = False
                    
    # Helper to render a block of lines
    def render_block(lines, is_safe):
        html_out = ""
        # User Request: Same content -> Green Highlight
        base_class = "diff-line diff-same" if is_safe else "diff-line"
        
        if is_safe and len(lines) > 6:
            head = lines[:2]
            middle = lines[2:-2]
            tail = lines[-2:]
            
            for line in head:
                html_out += f'<div class="{base_class}">{html.escape(line)}</div>'
            
            # For the folded part, we still wrap lines but maybe the summary itself is neutral
            middle_html = ''.join([f'<div class="{base_class}">{html.escape(line)}</div>' for line in middle])
            html_out += f'<div class="diff-details"><details><summary class="diff-summary">... {len(middle)} same lines ...</summary>{middle_html}</details></div>'
            
            for line in tail:
                html_out += f'<div class="{base_class}">{html.escape(line)}</div>'
        else:
            for line in lines:
                html_out += f'<div class="{base_class}">{html.escape(line)}</div>'
        return html_out

    # 2. Render Columns
    for i, item in enumerate(data_list):
        lines_html = ""
        current_lines = json_strs[i]
        
        if i == 0:
            # Render Reference using the Safe Mask
            # We need to group Ref lines by consecutive Safe/Unsafe status
            idx = 0
            while idx < len(ref_lines):
                start = idx
                current_status = safe_mask[idx]
                while idx < len(ref_lines) and safe_mask[idx] == current_status:
                    idx += 1
                end = idx
                
                segment = ref_lines[start:end]
                lines_html += render_block(segment, current_status)
        else:
            # Render Target using Opcodes, but respecting Safe Mask for 'equal' blocks
            matcher = difflib.SequenceMatcher(None, ref_lines, current_lines)
            for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                if tag == 'equal':
                    # This block matches Ref [i1:i2].
                    # We must check if this Ref block is GLOBALLY safe.
                    # It might be 'equal' here, but 'unsafe' in another target.
                    # If it's unsafe in another target, Ref will show it. So we must show it too to align.
                    # We need to split this block based on safe_mask[i1:i2]
                    
                    sub_idx = i1
                    target_sub_idx = j1
                    while sub_idx < i2:
                        sub_start = sub_idx
                        sub_status = safe_mask[sub_idx]
                        while sub_idx < i2 and safe_mask[sub_idx] == sub_status:
                            sub_idx += 1
                        sub_end = sub_idx
                        
                        # Calculate corresponding length in Target (it's equal, so same length)
                        length = sub_end - sub_start
                        target_sub_end = target_sub_idx + length
                        
                        segment = current_lines[target_sub_idx:target_sub_end]
                        lines_html += render_block(segment, sub_status)
                        
                        target_sub_idx = target_sub_end
                        
                elif tag == 'replace':
                    for line in current_lines[j1:j2]:
                        lines_html += f'<div class="diff-line diff-change">{html.escape(line)}</div>'
                elif tag == 'delete':
                    pass 
                elif tag == 'insert':
                    for line in current_lines[j1:j2]:
                        lines_html += f'<div class="diff-line diff-add">{html.escape(line)}</div>'
                        
        cols_html += f'<div class="diff-column"><div class="diff-header">{html.escape(item["name"])}</div><div class="diff-content">{lines_html}</div></div>'
        
    return f'<div class="diff-container">{cols_html}</div>'

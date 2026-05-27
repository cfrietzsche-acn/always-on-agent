import datetime

import anthropic

import tools as tools_module
from prompts import AUDIT_SYSTEM, TRIAGE_SYSTEM
from tools import TOOL_SCHEMAS, dispatch


def run(mode: str, repo_root: str, api_key: str, model: str = "claude-sonnet-4-6",
        trigger_message: str = None):
    tools_module.REPO_ROOT = repo_root

    system = TRIAGE_SYSTEM if mode == "triage" else AUDIT_SYSTEM
    system = system.replace("{date}", datetime.date.today().isoformat())

    client = anthropic.Anthropic(api_key=api_key)
    user_msg = trigger_message or f"Run the {mode} workflow now."
    messages = [{"role": "user", "content": user_msg}]

    print(f"\n[agent] mode={mode} model={model}\n")

    while True:
        with client.messages.stream(
            model=model,
            max_tokens=8192,
            system=system,
            tools=TOOL_SCHEMAS,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            response = stream.get_final_message()

        # Ensure any streamed reasoning text gets a newline before tool/end output
        print()

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  → {block.name}({block.input})")
                    result = dispatch(block.name, block.input)
                    preview = result[:120].replace("\n", " ")
                    print(f"    {preview}{'...' if len(result) > 120 else ''}\n")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
            # All results go in ONE user message — never one message per result
            messages.append({"role": "user", "content": tool_results})

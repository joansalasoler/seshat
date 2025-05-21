# -*- coding: utf-8 -*-

# Seshat: AI powered command palette
# Copyright (C) 2025 Joan Sala <contact@joansala.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import random
import gi
gi.require_version('Gdk', '4.0')

import asyncio
from seshat.actions import ChatProvider
from seshat.utils import ConfigManager

config = ConfigManager()
commands = config.get_commands()

PROMPT = """
You are a verification assistant tasked with evaluating the quality of a language model's output in the context of a text editor assistant. Given a user_input and the corresponding llm_output, your job is to determine how well the output follows the original assistant system prompt, task guidelines, and formatting requirements. Then, if your score is low or the LLM failed to fulfill the 'task', make a very small modification (change, add or remove a single word) to "llm_system_prompt" if you think that by making that modification the LLM will provide a betters answers for the failed 'task'. "llm_system_prompt" should contain the full original "llm_system_prompt" with your modification applied to it.

You must return a score between 0.0 and 1.0, where:

* 1.0 indicates perfect execution,
* 0.0 indicates a complete failure to follow the prompt or produce any valid output,
* Scores between reflect proportional adherence to expectations.

# Input:

A JSON object with the following fields:

{
  "user_input": {
    "task": "<string>",
    "selected_text": "<string>"
  },
  "llm_output": {
    "status": "success|error",
    "answers": ["<response1>", "<response2>", ...],
    "error_message": "<string>"
  },
  "llm_system_prompt": "<string">
}

# Evaluation Criteria:

1. Structural Compliance (0.0-1.0)
- The output must be a single JSON object with exactly the required fields.
- "status" must be "success" or "error".
- "answers" must be a non-empty array only if "status" is "success".
- "error_message" must be a non-empty string only if "status" is "error".

2. Task Fulfillment (0.0-1.0)

* For "success":
- Answers should clearly address the task, appropriately modify selected_text when required, and provide high-quality, varied, standalone alternatives.
- Language, tone, and formatting must match the selected_text unless the task specifies otherwise.

* For "error":
- Error must be appropriate and aligned with error-triggering rules (e.g., invalid task, empty text when required, nonsensical request).
- Error message must be user-friendly and fun.

3. Language Accuracy (0.0–1.0) — High Weight

- The language used in answers or error_message must match the language of selected_text unless the task explicitly requests a different language.
- All answers must be in a single, consistent language unless the task specifically calls for multilingual output.
- Any mismatch in language or inconsistency across answers should heavily penalize the score.
- Regional and formal/informal variations should be respected if indicated by context or task.
- Unless the tasks asks for something else, all the strings in 'answers' should be in the same language.

4. Formatting & Style Matching (0.0–1.0)

- Preserve casing, punctuation, spacing, and paragraph structure from selected_text unless explicitly instructed to change them.

- Tone and writing style should match that of the selected_text.

# Scoring Logic:

Return a single float score between 0.0 and 1.0 based on the lowest of the three sub-scores (structure, task, formatting). This reflects that failure in any area significantly compromises the output quality.

Additionally, return a brief natural language explanation in English (2-3 sentences) to justify the score (including which language is 'selected_text' written in, which language does 'task' request for the 'answers', and why or why not the language of 'answers' matches the user expectations).

A mismatch between the users expected language for 'answers' an the language used in 'answers' should result in total output score of 0.0

# Output Format:

{
  "score": <float between 0.0 and 1.0>,
  "explanation": "<brief justification>",
  "llm_system_prompt": "<new system prompt>"
}

Be strict, precise, and consistent. The score must reflect actual conformance to the editing assistant's expected behavior, structure, and quality.
"""

def build_verifier_messages(input, output, prompt):
    content = {
        "user_input": json.loads(input),
        "llm_output": json.loads(output),
        "llm_system_prompt": json.dumps(prompt),
    }

    return [{
        "role": "system",
        "content": PROMPT
    }, {
        "role": "user",
        "content": json.dumps(content)
    }]


verifier = ChatProvider()
verifier.set_default_model("gemma3:4b")
verifier.set_base_url("http://localhost:11434")
verifier._response_format = {
    "type": "object",
    "properties": {
        "score": {
            "type": "number"
        },
        "explanation": {
            "type": "string"
        },
        "llm_system_prompt": {
            "type": "string"
        },
    },
    "required": ["score", "explanation", "llm_system_prompt"]
}

provider = ChatProvider()
provider.set_default_model("deepseek-r1:7b")
provider.set_base_url("http://localhost:11434")
default_prompt = str(provider._base_prompt)

score_sum = 0
score_count = 0

for command in commands:
    if command.get("action_name") == "ai:query":
        if command.get("user_query") is not None:
            try:
                text = "patata"
                query = command.get("user_query")
                print(command.get("user_query"))

                messages = provider._build_messages("Give me a random word or short sentence in Catalan, Spanish or English", "")
                # print(messages)
                response = asyncio.run(provider._post_chat(messages))
                print(response)

                text = random.choice(json.loads(response)["answers"])
                messages = provider._build_messages(query, text)
                print(messages[1]["content"])
                response = asyncio.run(provider._post_chat(messages))
                print(response)

                prompt = messages[0]["content"]
                input = messages[1]["content"]
                output = response

                messages = build_verifier_messages(input, output, prompt)
                # print(messages)
                response = asyncio.run(verifier._post_chat(messages))
                print(response)

                response = json.loads(response)
                score = float(response["score"])
                score_sum += score
                score_count += 1

                if score < 0.8:
                    provider._base_prompt = response["llm_system_prompt"]

                print("average score = " + str(score_sum/score_count))
            except Exception as e:
                print(e)

print(provider._base_prompt)
